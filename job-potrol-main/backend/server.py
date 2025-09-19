from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import requests
import PyPDF2
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize Gemini LLM
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    location: str
    description: str
    requirements: str
    skills_extracted: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobCreate(BaseModel):
    title: str
    company: str = "Sample Company"
    location: str = "Remote"
    description: str
    requirements: str = ""

class Resume(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    text_content: str
    skills_extracted: List[str] = []
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobMatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resume_id: str
    job_id: str
    match_score: float
    matching_skills: List[str]
    missing_skills: List[str]
    explanation: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Convert ISO strings back to datetime objects from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key.endswith('_at') and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
    return item

async def extract_skills_with_llm(text: str, context: str = "job description") -> List[str]:
    """Extract skills from text using Gemini LLM"""
    try:
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"skills-extraction-{uuid.uuid4()}",
            system_message="You are a skilled HR expert who extracts technical and professional skills from text. Return only a comma-separated list of skills, no additional text or formatting."
        ).with_model("gemini", "gemini-2.0-flash")
        
        user_message = UserMessage(
            text=f"Extract all relevant skills from this {context}. Focus on technical skills, programming languages, frameworks, tools, and professional competencies. Text: {text[:2000]}"
        )
        
        response = await chat.send_message(user_message)
        
        # Parse the response to extract skills
        skills_text = response.strip()
        skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
        
        # Clean and filter skills (remove empty, very short, or generic terms)
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip().title()
            if len(skill) > 1 and not skill.lower() in ['and', 'or', 'the', 'with', 'for', 'in', 'on', 'at']:
                cleaned_skills.append(skill)
        
        return cleaned_skills[:20]  # Limit to top 20 skills
    except Exception as e:
        logging.error(f"Error extracting skills with LLM: {e}")
        return []

async def calculate_job_match(resume_skills: List[str], job_skills: List[str], resume_text: str, job_text: str) -> Dict[str, Any]:
    """Calculate match score and explanation using Gemini LLM"""
    try:
        # Calculate basic match score
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]
        
        matching_skills = []
        for job_skill in job_skills:
            for resume_skill in resume_skills:
                if job_skill.lower() == resume_skill.lower() or job_skill.lower() in resume_skill.lower() or resume_skill.lower() in job_skill.lower():
                    matching_skills.append(job_skill)
                    break
        
        missing_skills = [skill for skill in job_skills if skill.lower() not in [ms.lower() for ms in matching_skills]]
        
        if len(job_skills) > 0:
            match_score = (len(matching_skills) / len(job_skills)) * 100
        else:
            match_score = 0
        
        # Generate explanation using LLM
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"match-explanation-{uuid.uuid4()}",
            system_message="You are an expert career counselor who provides detailed explanations for job-candidate matches. Be concise but informative."
        ).with_model("gemini", "gemini-2.0-flash")
        
        explanation_prompt = f"""
        Analyze this job match:
        Match Score: {match_score:.1f}%
        Matching Skills: {', '.join(matching_skills)}
        Missing Skills: {', '.join(missing_skills)}
        
        Provide a brief explanation (2-3 sentences) of why this candidate is a {match_score:.1f}% match for this position.
        """
        
        user_message = UserMessage(text=explanation_prompt)
        explanation = await chat.send_message(user_message)
        
        return {
            "match_score": round(match_score, 1),
            "matching_skills": list(set(matching_skills)),
            "missing_skills": list(set(missing_skills)),
            "explanation": explanation.strip()
        }
    except Exception as e:
        logging.error(f"Error calculating job match: {e}")
        return {
            "match_score": 0,
            "matching_skills": [],
            "missing_skills": job_skills,
            "explanation": "Unable to generate match analysis at this time."
        }

# Fetch jobs from external API and populate database
async def populate_jobs_from_api():
    """Fetch jobs from jsonplaceholder and adapt them as job listings"""
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/posts")
        posts = response.json()
        
        job_templates = [
            {"title": "Software Engineer", "company": "TechCorp", "location": "San Francisco, CA"},
            {"title": "Frontend Developer", "company": "WebSolutions", "location": "New York, NY"},
            {"title": "Backend Developer", "company": "DataSystems", "location": "Austin, TX"},
            {"title": "Full Stack Developer", "company": "StartupInc", "location": "Seattle, WA"},
            {"title": "DevOps Engineer", "company": "CloudTech", "location": "Remote"},
            {"title": "Data Scientist", "company": "AILabs", "location": "Boston, MA"},
            {"title": "Product Manager", "company": "InnovateCorp", "location": "Los Angeles, CA"},
            {"title": "UX Designer", "company": "DesignStudio", "location": "Chicago, IL"},
            {"title": "QA Engineer", "company": "QualityFirst", "location": "Denver, CO"},
            {"title": "Mobile Developer", "company": "AppBuilder", "location": "Miami, FL"}
        ]
        
        jobs_created = 0
        for i, post in enumerate(posts[:30]):  # Limit to 30 jobs
            template = job_templates[i % len(job_templates)]
            
            # Create job description from post content
            job_description = f"""
            We are looking for a talented {template['title']} to join our growing team at {template['company']}.
            
            About the role:
            {post['body']}
            
            Key Responsibilities:
            • Develop and maintain high-quality software solutions
            • Collaborate with cross-functional teams
            • Participate in code reviews and technical discussions
            • Contribute to architectural decisions
            """
            
            requirements = _generate_requirements_for_role(template['title'])
            
            job_data = {
                "id": str(uuid.uuid4()),
                "title": template['title'],
                "company": template['company'],
                "location": template['location'],
                "description": job_description,
                "requirements": requirements,
                "skills_extracted": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Check if job already exists
            existing = await db.jobs.find_one({"title": job_data["title"], "company": job_data["company"]})
            if not existing:
                await db.jobs.insert_one(job_data)
                jobs_created += 1
        
        return jobs_created
    except Exception as e:
        logging.error(f"Error populating jobs: {e}")
        return 0

def _generate_requirements_for_role(title: str) -> str:
    """Generate requirements based on job title"""
    requirements_map = {
        "Software Engineer": "Bachelor's degree in Computer Science or related field. 3+ years of experience with Python, Java, or C++. Experience with cloud platforms and databases.",
        "Frontend Developer": "Strong experience with React, JavaScript, HTML5, CSS3. Knowledge of modern frontend tools and frameworks. Experience with responsive design.",
        "Backend Developer": "Proficiency in server-side languages (Python, Node.js, Java). Experience with REST APIs, databases, and cloud services.",
        "Full Stack Developer": "Experience with both frontend (React, Vue) and backend (Node.js, Python) technologies. Knowledge of databases and cloud platforms.",
        "DevOps Engineer": "Experience with CI/CD pipelines, Docker, Kubernetes. Knowledge of AWS/Azure/GCP. Infrastructure as code experience.",
        "Data Scientist": "Strong background in Python, R, SQL. Experience with machine learning frameworks. Statistical analysis and data visualization skills.",
        "Product Manager": "5+ years of product management experience. Strong analytical and communication skills. Experience with agile methodologies.",
        "UX Designer": "Portfolio demonstrating user-centered design. Proficiency in design tools (Figma, Sketch). User research experience.",
        "QA Engineer": "Experience with automated testing frameworks. Knowledge of testing methodologies. Programming skills in Python or Java.",
        "Mobile Developer": "Experience with React Native, Flutter, or native iOS/Android development. App store publishing experience."
    }
    return requirements_map.get(title, "Relevant experience and strong problem-solving skills required.")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Job Portal API"}

@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(
    search: Optional[str] = Query(None, description="Search by job title"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company: Optional[str] = Query(None, description="Filter by company")
):
    """Get all jobs with optional search and filters"""
    # Ensure we have jobs in database
    job_count = await db.jobs.count_documents({})
    if job_count == 0:
        await populate_jobs_from_api()
    
    # Build query
    query = {}
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if company:
        query["company"] = {"$regex": company, "$options": "i"}
    
    jobs = await db.jobs.find(query).to_list(100)
    return [Job(**parse_from_mongo(job)) for job in jobs]

@api_router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process PDF resume"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read PDF content
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Extract skills using LLM
        skills = await extract_skills_with_llm(text_content, "resume")
        
        # Save resume to database
        resume_data = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "text_content": text_content,
            "skills_extracted": skills,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.resumes.insert_one(resume_data)
        
        return {
            "message": "Resume uploaded successfully",
            "resume_id": resume_data["id"],
            "skills_extracted": skills,
            "text_preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
        }
    
    except Exception as e:
        logging.error(f"Error processing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@api_router.get("/resume/{resume_id}")
async def get_resume(resume_id: str):
    """Get resume details"""
    resume = await db.resumes.find_one({"id": resume_id})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return Resume(**parse_from_mongo(resume))

@api_router.post("/jobs/{job_id}/analyze")
async def analyze_job(job_id: str):
    """Analyze job description and extract skills"""
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Extract skills if not already done
    if not job.get("skills_extracted"):
        job_text = f"{job['title']} {job['description']} {job['requirements']}"
        skills = await extract_skills_with_llm(job_text, "job description")
        
        # Update job with extracted skills
        await db.jobs.update_one(
            {"id": job_id},
            {"$set": {"skills_extracted": skills}}
        )
        job["skills_extracted"] = skills
    
    return {"job_id": job_id, "skills_extracted": job["skills_extracted"]}

@api_router.post("/match/{resume_id}")
async def get_job_matches(resume_id: str):
    """Get job recommendations for a resume"""
    resume = await db.resumes.find_one({"id": resume_id})
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Get all jobs
    jobs = await db.jobs.find().to_list(100)
    matches = []
    
    for job in jobs:
        # Extract job skills if not already done
        if not job.get("skills_extracted"):
            job_text = f"{job['title']} {job['description']} {job['requirements']}"
            job_skills = await extract_skills_with_llm(job_text, "job description")
            await db.jobs.update_one(
                {"id": job["id"]},
                {"$set": {"skills_extracted": job_skills}}
            )
            job["skills_extracted"] = job_skills
        
        # Calculate match
        match_result = await calculate_job_match(
            resume["skills_extracted"],
            job["skills_extracted"],
            resume["text_content"],
            job["description"]
        )
        
        # Save match to database
        match_data = {
            "id": str(uuid.uuid4()),
            "resume_id": resume_id,
            "job_id": job["id"],
            "match_score": match_result["match_score"],
            "matching_skills": match_result["matching_skills"],
            "missing_skills": match_result["missing_skills"],
            "explanation": match_result["explanation"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Check if match already exists
        existing_match = await db.matches.find_one({
            "resume_id": resume_id,
            "job_id": job["id"]
        })
        
        if existing_match:
            await db.matches.update_one(
                {"resume_id": resume_id, "job_id": job["id"]},
                {"$set": match_data}
            )
        else:
            await db.matches.insert_one(match_data)
        
        # Add job details to match result
        match_result["job"] = Job(**parse_from_mongo(job))
        matches.append(match_result)
    
    # Sort by match score
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "resume_id": resume_id,
        "total_matches": len(matches),
        "matches": matches[:10]  # Return top 10 matches
    }

@api_router.get("/matches/{resume_id}", response_model=List[JobMatch])
async def get_saved_matches(resume_id: str):
    """Get saved job matches for a resume"""
    matches = await db.matches.find({"resume_id": resume_id}).to_list(100)
    return [JobMatch(**parse_from_mongo(match)) for match in matches]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()