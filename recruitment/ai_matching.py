"""
AI Resume Matching System
Implements both approaches as described in the thesis:
- Approach 1: SentenceTransformer embedding + cosine similarity + weighted scoring
- Approach 2: Groq LLM (Llama 70B) + RAG for enhanced analysis
"""

import re
import json
import pdfplumber
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
from django.conf import settings

# Load the embedding model (BAAI/bge-m3 supporting English, French, Arabic with 8192-token context)
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('BAAI/bge-m3')
    return _model


def get_groq_client():
    return Groq(api_key=settings.GROQ_API_KEY)


# ============================================================
# TEXT EXTRACTION & PREPROCESSING
# ============================================================

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF resume using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text.strip()


def preprocess_text(text):
    """Clean and normalize text for NLP analysis."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:@/\-+#()]', '', text)
    return text.strip()


def build_job_context(job_offer):
    """Build unified job context from JobOffer, Job, and JobMission models."""
    job = job_offer.job
    
    context_parts = [
        f"Job Title: {job_offer.title}",
        f"Job Description: {job_offer.description}",
        f"Category: {job.category}" if job.category else "",
        f"Required Skills: {job.required_skills}",
        f"Required Education: {job.required_education}" if job.required_education else "",
        f"Required Certifications: {job.required_certifications}" if job.required_certifications else "",
        f"Searched Profiles: {job_offer.searched_profiles}" if job_offer.searched_profiles else "",
    ]
    
    missions = job.missions.all()
    if missions:
        mission_text = "Job Missions: " + "; ".join([m.description for m in missions])
        context_parts.append(mission_text)
    
    return "\n".join([p for p in context_parts if p])


# ============================================================
# APPROACH 1: EMBEDDING MODEL (SentenceTransformer)
# ============================================================

def compute_semantic_similarity(text1, text2):
    """Compute cosine similarity between two texts using SentenceTransformer."""
    model = get_embedding_model()
    embeddings = model.encode([text1, text2])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(max(0, min(1, similarity)))


def compute_skills_score(resume_text, required_skills_str):
    """Calculate skills matching score."""
    if not required_skills_str:
        return 100.0, []
    
    required_skills = [s.strip().lower() for s in required_skills_str.split(',') if s.strip()]
    if not required_skills:
        return 100.0, []
    
    resume_lower = resume_text.lower()
    matched = []
    
    model = get_embedding_model()
    
    for skill in required_skills:
        # Direct keyword match
        if skill in resume_lower:
            matched.append(skill)
            continue
        
        # Semantic match for skills not found by keyword
        skill_embedding = model.encode([skill])
        # Check against resume chunks
        resume_words = resume_lower.split()
        chunk_size = 5
        best_sim = 0
        for i in range(0, len(resume_words), chunk_size):
            chunk = ' '.join(resume_words[i:i+chunk_size])
            chunk_embedding = model.encode([chunk])
            sim = cosine_similarity(skill_embedding, chunk_embedding)[0][0]
            best_sim = max(best_sim, sim)
        
        if best_sim > 0.6:
            matched.append(skill)
    
    score = (len(matched) / len(required_skills)) * 100
    return score, matched


def compute_education_score(resume_text, required_education):
    """Calculate education level matching score."""
    if not required_education:
        return 100.0
    
    education_keywords = [
        'bachelor', 'master', 'phd', 'doctorate', 'engineering', 'degree',
        'licence', 'ingénieur', 'bac+5', 'bac+3', 'bac+2', 'diploma',
        'university', 'computer science', 'informatique', 'software',
        'cybersecurity', 'data science', 'network', 'telecommunications'
    ]
    
    resume_lower = resume_text.lower()
    required_lower = required_education.lower()
    
    # Semantic similarity between education requirement and resume
    similarity = compute_semantic_similarity(required_lower, resume_lower)
    
    # Keyword-based bonus
    found_count = sum(1 for kw in education_keywords if kw in resume_lower)
    keyword_bonus = min(found_count * 5, 30)
    
    score = (similarity * 70) + keyword_bonus
    return min(100, score)


def compute_certification_score(resume_text, required_certifications):
    """Calculate certification matching score."""
    if not required_certifications:
        return 100.0
    
    certs = [c.strip().lower() for c in required_certifications.split(',') if c.strip()]
    if not certs:
        return 100.0
    
    resume_lower = resume_text.lower()
    matched = sum(1 for cert in certs if cert in resume_lower)
    
    return (matched / len(certs)) * 100


def compute_profile_score(resume_text, job):
    """
    Combined Profile Score = 0.50 * Education + 0.35 * Skills + 0.15 * Certification
    (As defined in thesis section 2.4.6.1.4)
    """
    education_score = compute_education_score(resume_text, job.required_education)
    skills_score, matched_skills = compute_skills_score(resume_text, job.required_skills)
    cert_score = compute_certification_score(resume_text, job.required_certifications)
    
    profile_score = (0.50 * education_score) + (0.35 * skills_score) + (0.15 * cert_score)
    
    return profile_score, matched_skills


def compute_mission_score(resume_text, job):
    """Calculate mission relevance score using semantic similarity."""
    missions = job.missions.all()
    if not missions:
        return 100.0, []
    
    matched_missions = []
    total_score = 0
    
    for mission in missions:
        sim = compute_semantic_similarity(mission.description, resume_text)
        mission_score = sim * 100
        total_score += mission_score
        if mission_score > 40:
            matched_missions.append(mission.description)
    
    avg_score = total_score / len(missions) if missions else 0
    return avg_score, matched_missions


def compute_category_score(resume_text, job):
    """Check professional domain alignment."""
    if not job.category:
        return 100.0
    
    sim = compute_semantic_similarity(job.category, resume_text)
    return sim * 100


def compute_quality_score(resume_text):
    """Evaluate resume structure and completeness."""
    quality_sections = {
        'education': ['education', 'academic', 'university', 'degree', 'school', 'formation'],
        'experience': ['experience', 'work', 'employment', 'professional', 'position'],
        'skills': ['skills', 'competencies', 'technologies', 'tools', 'programming'],
        'contact': ['email', 'phone', 'address', 'linkedin', 'github', '@'],
    }
    
    resume_lower = resume_text.lower()
    found_sections = 0
    
    for section, keywords in quality_sections.items():
        if any(kw in resume_lower for kw in keywords):
            found_sections += 1
    
    # Length quality (longer resumes tend to be more detailed)
    word_count = len(resume_text.split())
    length_score = min(100, (word_count / 300) * 100)
    
    section_score = (found_sections / len(quality_sections)) * 100
    
    return (0.6 * section_score) + (0.4 * length_score)


def approach1_analyze(resume_text, job_offer):
    """
    APPROACH 1: SentenceTransformer Embedding Model
    Implements the full scoring pipeline from thesis section 2.4.6:
    FinalScore = (0.35 * Profile) + (0.30 * Semantic) + (0.20 * Mission) + (0.10 * Category) + (0.05 * Quality)
    """
    job = job_offer.job
    job_context = build_job_context(job_offer)
    clean_resume = preprocess_text(resume_text)
    clean_job = preprocess_text(job_context)
    
    # Calculate individual scores
    profile_score, matched_skills = compute_profile_score(clean_resume, job)
    semantic_score = compute_semantic_similarity(clean_resume, clean_job) * 100
    mission_score, matched_missions = compute_mission_score(clean_resume, job)
    category_score = compute_category_score(clean_resume, job)
    quality_score = compute_quality_score(resume_text)
    
    # Weighted final score (thesis formula)
    final_score = (
        (0.35 * profile_score) +
        (0.30 * semantic_score) +
        (0.20 * mission_score) +
        (0.10 * category_score) +
        (0.05 * quality_score)
    )
    
    return {
        'final_score': round(final_score, 2),
        'profile_score': round(profile_score, 2),
        'semantic_score': round(semantic_score, 2),
        'mission_score': round(mission_score, 2),
        'category_score': round(category_score, 2),
        'quality_score': round(quality_score, 2),
        'matched_skills': matched_skills,
        'matched_missions': matched_missions,
    }


# ============================================================
# APPROACH 2: GROQ + RAG (Llama 70B)
# ============================================================

def approach2_analyze(resume_text, job_offer):
    """
    APPROACH 2: Groq API + RAG with Llama 70B
    Uses RAG to provide job context and resume to the LLM for enhanced analysis.
    """
    job_context = build_job_context(job_offer)
    
    # Build RAG context
    rag_context = f"""
=== JOB OFFER CONTEXT (Retrieved from Database) ===
{job_context}

=== CANDIDATE RESUME TEXT ===
{resume_text[:4000]}
"""
    
    prompt = f"""You are an expert AI recruitment analyst. Analyze this candidate's resume against the job requirements using the RAG context provided.

{rag_context}

Provide your analysis as a valid JSON object with these exact fields:
{{
    "ai_score": <float 0-100>,
    "strengths": ["list", "of", "strengths"],
    "weaknesses": ["list", "of", "weaknesses"],
    "matched_skills": ["matched", "skill1", "skill2"],
    "summary": "2-3 sentence overall assessment"
}}

Be specific and accurate. Score based on:
- Profile match (skills, education, certifications): 35%
- Semantic similarity to job description: 30%
- Mission/experience relevance: 20%
- Domain/category alignment: 10%
- Resume quality: 5%

Return ONLY valid JSON, no other text."""

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert AI recruitment analyst. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        # Handle cases where LLM wraps JSON in code blocks
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        print(f"Groq API error in approach 2: {e}")
        return None


# ============================================================
# COMBINED ANALYSIS (Both Approaches)
# ============================================================

def analyze_resume(resume_path, job_offer):
    """
    Full AI analysis pipeline combining both approaches.
    Returns comprehensive analysis results.
    """
    # Extract and preprocess resume text
    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text:
        return {
            'error': 'Could not extract text from PDF',
            'final_score': 0,
        }
    
    # APPROACH 1: Embedding-based analysis
    approach1_results = approach1_analyze(resume_text, job_offer)
    
    # APPROACH 2: Groq + RAG analysis
    approach2_results = approach2_analyze(resume_text, job_offer)
    
    # Combine results
    if approach2_results:
        # Average the scores from both approaches for robustness
        combined_score = (approach1_results['final_score'] + approach2_results.get('ai_score', approach1_results['final_score'])) / 2
        
        strengths = approach2_results.get('strengths', [])
        weaknesses = approach2_results.get('weaknesses', [])
        summary = approach2_results.get('summary', '')
        
        # Merge matched skills from both approaches
        all_matched_skills = list(set(
            approach1_results['matched_skills'] + 
            approach2_results.get('matched_skills', [])
        ))
    else:
        combined_score = approach1_results['final_score']
        strengths = []
        weaknesses = []
        summary = f"Embedding-based analysis complete. Overall match: {approach1_results['final_score']}%"
        all_matched_skills = approach1_results['matched_skills']
    
    return {
        'resume_text': resume_text,
        'final_score': round(combined_score, 2),
        'profile_score': approach1_results['profile_score'],
        'semantic_score': approach1_results['semantic_score'],
        'mission_score': approach1_results['mission_score'],
        'category_score': approach1_results['category_score'],
        'quality_score': approach1_results['quality_score'],
        'matched_skills': all_matched_skills,
        'matched_missions': approach1_results['matched_missions'],
        'strengths': strengths,
        'weaknesses': weaknesses,
        'summary': summary,
        'approach1_score': approach1_results['final_score'],
        'approach2_score': approach2_results.get('ai_score') if approach2_results else None,
    }


# ============================================================
# AI SUMMARY GENERATION (Using Groq + RAG)
# ============================================================

def generate_ai_summary(resume_text, job_offer, scores):
    """Generate human-readable AI summary using Groq + RAG."""
    job_context = build_job_context(job_offer)
    
    prompt = f"""Based on the following recruitment analysis, generate a professional summary:

JOB CONTEXT:
{job_context}

RESUME EXCERPT:
{resume_text[:2000]}

ANALYSIS SCORES:
- Overall Score: {scores.get('final_score', 'N/A')}%
- Profile Match: {scores.get('profile_score', 'N/A')}%
- Semantic Similarity: {scores.get('semantic_score', 'N/A')}%
- Mission Relevance: {scores.get('mission_score', 'N/A')}%
- Category Match: {scores.get('category_score', 'N/A')}%
- Resume Quality: {scores.get('quality_score', 'N/A')}%
- Matched Skills: {', '.join(scores.get('matched_skills', []))}

Write a concise 3-4 sentence professional assessment summary for the HR manager.
Focus on: key strengths, areas of concern, and overall recommendation."""

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert recruitment analyst. Write clear, professional assessments."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI Summary unavailable: {str(e)}"
