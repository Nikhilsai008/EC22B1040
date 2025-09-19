import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Progress } from "./components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Search, Upload, FileText, Briefcase, Star, MapPin, Building2, CheckCircle, XCircle, TrendingUp } from "lucide-react";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Job Listings Page
const JobListings = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [companyFilter, setCompanyFilter] = useState("");

  useEffect(() => {
    fetchJobs();
  }, [searchTerm, locationFilter, companyFilter]);

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (locationFilter) params.append('location', locationFilter);
      if (companyFilter) params.append('company', companyFilter);
      
      const response = await axios.get(`${API}/jobs?${params}`);
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeJob = async (jobId) => {
    try {
      await axios.post(`${API}/jobs/${jobId}/analyze`);
      fetchJobs(); // Refresh to get updated skills
    } catch (error) {
      console.error('Error analyzing job:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-4">Find Your Perfect Job</h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Discover amazing opportunities tailored to your skills with AI-powered job matching
          </p>
        </div>

        {/* Search and Filters */}
        <Card className="mb-8 shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search job titles..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Location..."
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                  className="pl-10 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="relative">
                <Building2 className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Company..."
                  value={companyFilter}
                  onChange={(e) => setCompanyFilter(e.target.value)}
                  className="pl-10 border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Jobs Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="h-4 bg-slate-200 rounded mb-4"></div>
                  <div className="h-3 bg-slate-200 rounded mb-2"></div>
                  <div className="h-3 bg-slate-200 rounded mb-4"></div>
                  <div className="h-8 bg-slate-200 rounded"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <Card key={job.id} className="group hover:shadow-xl transition-all duration-300 border-0 bg-white/90 backdrop-blur-sm hover:bg-white/95">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg font-semibold text-slate-800 group-hover:text-blue-600 transition-colors">
                        {job.title}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2 text-slate-600 mt-1">
                        <Building2 className="h-4 w-4" />
                        {job.company}
                      </CardDescription>
                    </div>
                    <Briefcase className="h-5 w-5 text-blue-500" />
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <MapPin className="h-4 w-4" />
                    {job.location}
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600 mb-4 line-clamp-3">
                    {job.description.substring(0, 150)}...
                  </p>
                  
                  {job.skills_extracted && job.skills_extracted.length > 0 ? (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-slate-700 mb-2">Key Skills:</h4>
                      <div className="flex flex-wrap gap-1">
                        {job.skills_extracted.slice(0, 4).map((skill, index) => (
                          <Badge key={index} variant="secondary" className="text-xs bg-blue-100 text-blue-700 hover:bg-blue-200">
                            {skill}
                          </Badge>
                        ))}
                        {job.skills_extracted.length > 4 && (
                          <Badge variant="outline" className="text-xs">
                            +{job.skills_extracted.length - 4} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => analyzeJob(job.id)}
                      className="mb-4 text-blue-600 border-blue-200 hover:bg-blue-50"
                    >
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Analyze Skills
                    </Button>
                  )}
                  
                  <div className="flex gap-2">
                    <Button size="sm" className="flex-1 bg-blue-600 hover:bg-blue-700">
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {jobs.length === 0 && !loading && (
          <Card className="text-center py-12">
            <CardContent>
              <Briefcase className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-800 mb-2">No jobs found</h3>
              <p className="text-slate-600">Try adjusting your search criteria.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

// Resume Upload Page
const ResumeUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a PDF file');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/resume/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);
      
      // Store resume ID for later use
      localStorage.setItem('currentResumeId', response.data.resume_id);
      
    } catch (error) {
      console.error('Error uploading resume:', error);
      setError(error.response?.data?.detail || 'Error uploading resume');
    } finally {
      setUploading(false);
    }
  };

  const viewMatches = () => {
    if (uploadResult?.resume_id) {
      navigate(`/matches/${uploadResult.resume_id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-slate-800 mb-4">Upload Your Resume</h1>
            <p className="text-lg text-slate-600">
              Let our AI analyze your skills and find the perfect job matches
            </p>
          </div>

          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardContent className="p-8">
              {!uploadResult ? (
                <div className="space-y-6">
                  {/* File Upload Area */}
                  <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-emerald-400 transition-colors">
                    <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                    <div className="space-y-2">
                      <h3 className="text-lg font-medium text-slate-800">
                        Choose your resume file
                      </h3>
                      <p className="text-slate-600">Upload a PDF file to get started</p>
                      <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 file:cursor-pointer cursor-pointer"
                      />
                    </div>
                  </div>

                  {file && (
                    <Alert className="border-emerald-200 bg-emerald-50">
                      <FileText className="h-4 w-4 text-emerald-600" />
                      <AlertDescription className="text-emerald-800">
                        Selected: {file.name}
                      </AlertDescription>
                    </Alert>
                  )}

                  {error && (
                    <Alert className="border-red-200 bg-red-50">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <AlertDescription className="text-red-800">
                        {error}
                      </AlertDescription>
                    </Alert>
                  )}

                  <Button
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300"
                    size="lg"
                  >
                    {uploading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                        Processing Resume...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload & Analyze
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Success Message */}
                  <Alert className="border-emerald-200 bg-emerald-50">
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                    <AlertDescription className="text-emerald-800">
                      Resume uploaded and analyzed successfully!
                    </AlertDescription>
                  </Alert>

                  {/* Extracted Skills */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 mb-3">
                      Skills Extracted from Your Resume:
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {uploadResult.skills_extracted.map((skill, index) => (
                        <Badge key={index} className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200 px-3 py-1">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Preview */}
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800 mb-3">
                      Resume Preview:
                    </h3>
                    <div className="bg-slate-50 rounded p-4 text-sm text-slate-700 max-h-40 overflow-y-auto">
                      {uploadResult.text_preview}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3">
                    <Button onClick={viewMatches} className="flex-1 bg-emerald-600 hover:bg-emerald-700">
                      <Star className="h-4 w-4 mr-2" />
                      Find Job Matches
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setUploadResult(null);
                        setFile(null);
                      }}
                      className="border-slate-300 hover:bg-slate-50"
                    >
                      Upload Another
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Job Matches Page
const JobMatches = () => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const resumeId = localStorage.getItem('currentResumeId');

  useEffect(() => {
    if (resumeId) {
      fetchMatches();
    } else {
      setError('No resume found. Please upload a resume first.');
      setLoading(false);
    }
  }, [resumeId]);

  const fetchMatches = async () => {
    try {
      const response = await axios.post(`${API}/match/${resumeId}`);
      setMatches(response.data.matches);
    } catch (error) {
      console.error('Error fetching matches:', error);
      setError('Error fetching job matches');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-emerald-100';
    if (score >= 60) return 'bg-blue-100';
    if (score >= 40) return 'bg-orange-100';
    return 'bg-red-100';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-violet-50 to-purple-50 flex items-center justify-center">
        <Card className="p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-violet-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-lg text-slate-600">Analyzing your profile and finding perfect matches...</p>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-violet-50 to-purple-50 flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-800 mb-2">Error</h2>
          <p className="text-slate-600 mb-4">{error}</p>
          <Link to="/upload">
            <Button className="bg-violet-600 hover:bg-violet-700">
              Upload Resume
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-4">Your Job Matches</h1>
          <p className="text-lg text-slate-600">
            AI-powered recommendations based on your skills and experience
          </p>
        </div>

        {matches.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <Star className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-800 mb-2">No matches found</h3>
              <p className="text-slate-600">We couldn't find any suitable job matches at the moment.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {matches.map((match, index) => (
              <Card key={index} className="shadow-lg border-0 bg-white/90 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
                <CardContent className="p-6">
                  <div className="flex flex-col lg:flex-row gap-6">
                    {/* Job Info */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-xl font-semibold text-slate-800 mb-1">
                            {match.job.title}
                          </h3>
                          <div className="flex items-center gap-4 text-slate-600">
                            <div className="flex items-center gap-1">
                              <Building2 className="h-4 w-4" />
                              {match.job.company}
                            </div>
                            <div className="flex items-center gap-1">
                              <MapPin className="h-4 w-4" />
                              {match.job.location}
                            </div>
                          </div>
                        </div>
                        
                        {/* Match Score */}
                        <div className={`text-center p-3 rounded-lg ${getScoreBg(match.match_score)}`}>
                          <div className={`text-2xl font-bold ${getScoreColor(match.match_score)}`}>
                            {match.match_score}%
                          </div>
                          <div className="text-xs text-slate-600">Match</div>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="mb-4">
                        <Progress value={match.match_score} className="h-2" />
                      </div>

                      {/* Explanation */}
                      <p className="text-slate-700 mb-4 bg-slate-50 p-3 rounded-lg">
                        {match.explanation}
                      </p>

                      {/* Skills Comparison */}
                      <Tabs defaultValue="matching" className="w-full">
                        <TabsList className="grid w-full grid-cols-2">
                          <TabsTrigger value="matching" className="text-sm">
                            Matching Skills ({match.matching_skills.length})
                          </TabsTrigger>
                          <TabsTrigger value="missing" className="text-sm">
                            Missing Skills ({match.missing_skills.length})
                          </TabsTrigger>
                        </TabsList>
                        
                        <TabsContent value="matching" className="mt-3">
                          <div className="flex flex-wrap gap-2">
                            {match.matching_skills.map((skill, idx) => (
                              <Badge key={idx} className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                {skill}
                              </Badge>
                            ))}
                            {match.matching_skills.length === 0 && (
                              <p className="text-slate-500 text-sm">No matching skills found</p>
                            )}
                          </div>
                        </TabsContent>
                        
                        <TabsContent value="missing" className="mt-3">
                          <div className="flex flex-wrap gap-2">
                            {match.missing_skills.map((skill, idx) => (
                              <Badge key={idx} variant="outline" className="border-orange-300 text-orange-700">
                                <XCircle className="h-3 w-3 mr-1" />
                                {skill}
                              </Badge>
                            ))}
                            {match.missing_skills.length === 0 && (
                              <p className="text-slate-500 text-sm">No missing skills - perfect match!</p>
                            )}
                          </div>
                        </TabsContent>
                      </Tabs>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3 mt-6 pt-4 border-t border-slate-200">
                    <Button className="bg-violet-600 hover:bg-violet-700">
                      Apply Now
                    </Button>
                    <Button variant="outline" className="border-slate-300 hover:bg-slate-50">
                      Save Job
                    </Button>
                    <Button variant="outline" className="border-slate-300 hover:bg-slate-50">
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Main Navigation
const Navigation = () => {
  return (
    <nav className="bg-white/95 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Briefcase className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-slate-800">SkillMatch</span>
          </Link>
          
          <div className="flex items-center space-x-6">
            <Link to="/" className="text-slate-600 hover:text-blue-600 transition-colors">
              Jobs
            </Link>
            <Link to="/upload" className="text-slate-600 hover:text-blue-600 transition-colors">
              Upload Resume
            </Link>
            <Link to="/matches" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              My Matches
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Matches Route Handler
const MatchesRoute = () => {
  const resumeId = localStorage.getItem('currentResumeId');
  
  if (!resumeId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-violet-50 to-purple-50 flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-800 mb-2">No Resume Found</h2>
          <p className="text-slate-600 mb-4">Please upload your resume first to see job matches.</p>
          <Link to="/upload">
            <Button className="bg-violet-600 hover:bg-violet-700">
              Upload Resume
            </Button>
          </Link>
        </Card>
      </div>
    );
  }
  
  return <JobMatches />;
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<JobListings />} />
          <Route path="/upload" element={<ResumeUpload />} />
          <Route path="/matches" element={<MatchesRoute />} />
          <Route path="/matches/:resumeId" element={<JobMatches />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;