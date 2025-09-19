import requests
import sys
import json
import io
from datetime import datetime
import time

class JobPortalAPITester:
    def __init__(self, base_url="https://skillmatch-44.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.resume_id = None
        self.job_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_get_jobs(self):
        """Test getting job listings"""
        success, response = self.run_test(
            "Get Jobs",
            "GET", 
            "jobs",
            200
        )
        if success and isinstance(response, list) and len(response) > 0:
            self.job_id = response[0].get('id')
            print(f"   Found {len(response)} jobs, using job_id: {self.job_id}")
        return success

    def test_search_jobs(self):
        """Test job search functionality"""
        success, response = self.run_test(
            "Search Jobs (Software)",
            "GET",
            "jobs?search=Software",
            200
        )
        return success

    def test_filter_jobs_by_location(self):
        """Test job filtering by location"""
        success, response = self.run_test(
            "Filter Jobs by Location",
            "GET",
            "jobs?location=Remote",
            200
        )
        return success

    def test_filter_jobs_by_company(self):
        """Test job filtering by company"""
        success, response = self.run_test(
            "Filter Jobs by Company",
            "GET",
            "jobs?company=TechCorp",
            200
        )
        return success

    def create_test_pdf(self):
        """Create a proper test PDF using reportlab"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Add resume content
            p.drawString(100, 750, "JOHN DOE")
            p.drawString(100, 730, "Software Engineer")
            p.drawString(100, 710, "Email: john.doe@email.com")
            p.drawString(100, 690, "Phone: (555) 123-4567")
            
            p.drawString(100, 650, "SKILLS:")
            p.drawString(120, 630, "• Python, JavaScript, React, Node.js")
            p.drawString(120, 610, "• MongoDB, PostgreSQL, MySQL")
            p.drawString(120, 590, "• AWS, Docker, Kubernetes")
            p.drawString(120, 570, "• Machine Learning, Data Analysis")
            
            p.drawString(100, 530, "EXPERIENCE:")
            p.drawString(120, 510, "Senior Software Engineer - TechCorp (2020-2024)")
            p.drawString(120, 490, "• Developed web applications using React and Python")
            p.drawString(120, 470, "• Implemented microservices architecture")
            p.drawString(120, 450, "• Led team of 5 developers")
            
            p.drawString(100, 410, "EDUCATION:")
            p.drawString(120, 390, "Bachelor of Science in Computer Science")
            p.drawString(120, 370, "University of Technology (2016-2020)")
            
            p.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback to simple text if reportlab not available
            return b"Simple PDF content for testing - John Doe, Software Engineer with Python, React, Node.js, MongoDB experience"

    def test_resume_upload(self):
        """Test resume upload functionality"""
        # Create test PDF content
        pdf_content = self.create_test_pdf()
        
        files = {
            'file': ('test_resume.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        success, response = self.run_test(
            "Upload Resume",
            "POST",
            "resume/upload",
            200,
            files=files
        )
        
        if success and 'resume_id' in response:
            self.resume_id = response['resume_id']
            print(f"   Resume uploaded with ID: {self.resume_id}")
            print(f"   Skills extracted: {response.get('skills_extracted', [])}")
        
        return success

    def test_get_resume(self):
        """Test getting resume details"""
        if not self.resume_id:
            print("❌ Skipping - No resume_id available")
            return False
            
        success, response = self.run_test(
            "Get Resume Details",
            "GET",
            f"resume/{self.resume_id}",
            200
        )
        return success

    def test_analyze_job(self):
        """Test job analysis for skill extraction"""
        if not self.job_id:
            print("❌ Skipping - No job_id available")
            return False
            
        success, response = self.run_test(
            "Analyze Job Skills",
            "POST",
            f"jobs/{self.job_id}/analyze",
            200
        )
        
        if success:
            print(f"   Skills extracted: {response.get('skills_extracted', [])}")
        
        return success

    def test_job_matching(self):
        """Test AI-powered job matching"""
        if not self.resume_id:
            print("❌ Skipping - No resume_id available")
            return False
            
        print("   This may take a few seconds for AI processing...")
        success, response = self.run_test(
            "Generate Job Matches",
            "POST",
            f"match/{self.resume_id}",
            200
        )
        
        if success:
            print(f"   Total matches found: {response.get('total_matches', 0)}")
            matches = response.get('matches', [])
            if matches:
                print(f"   Top match score: {matches[0].get('match_score', 0)}%")
                print(f"   Top match explanation: {matches[0].get('explanation', 'N/A')[:100]}...")
        
        return success

    def test_get_saved_matches(self):
        """Test getting saved job matches"""
        if not self.resume_id:
            print("❌ Skipping - No resume_id available")
            return False
            
        success, response = self.run_test(
            "Get Saved Matches",
            "GET",
            f"matches/{self.resume_id}",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} saved matches")
        
        return success

def main():
    print("🚀 Starting Job Portal API Testing...")
    print("=" * 60)
    
    tester = JobPortalAPITester()
    
    # Test sequence
    test_results = []
    
    # Basic API tests
    test_results.append(("Root Endpoint", tester.test_root_endpoint()))
    test_results.append(("Get Jobs", tester.test_get_jobs()))
    test_results.append(("Search Jobs", tester.test_search_jobs()))
    test_results.append(("Filter by Location", tester.test_filter_jobs_by_location()))
    test_results.append(("Filter by Company", tester.test_filter_jobs_by_company()))
    
    # Resume and AI processing tests
    test_results.append(("Resume Upload", tester.test_resume_upload()))
    test_results.append(("Get Resume", tester.test_get_resume()))
    test_results.append(("Analyze Job", tester.test_analyze_job()))
    
    # AI matching tests (these may take longer)
    print("\n🤖 Testing AI-powered features (may take longer)...")
    test_results.append(("Job Matching", tester.test_job_matching()))
    test_results.append(("Get Saved Matches", tester.test_get_saved_matches()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = []
    failed_tests = []
    
    for test_name, result in test_results:
        if result:
            passed_tests.append(test_name)
        else:
            failed_tests.append(test_name)
    
    print(f"✅ Passed: {len(passed_tests)}/{len(test_results)} tests")
    if passed_tests:
        for test in passed_tests:
            print(f"   ✓ {test}")
    
    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)}/{len(test_results)} tests")
        for test in failed_tests:
            print(f"   ✗ {test}")
    
    print(f"\n🎯 Overall Success Rate: {(len(passed_tests)/len(test_results)*100):.1f}%")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())