"""
AI Chatbot Assistant - "Recruitment Assistant - Algérie Télécom Carrières"
Uses Groq API (Llama 70B) + RAG for contextual responses.
The chatbot retrieves relevant job offers from the database to provide
accurate, context-aware responses to candidate questions.
"""

import json
from groq import Groq
from django.conf import settings
from recruitment.models import JobOffer, Job


def get_groq_client():
    return Groq(api_key=settings.GROQ_API_KEY)


def get_job_offers_context():
    """RAG: Retrieve active job offers from database for chatbot context."""
    offers = JobOffer.objects.filter(status='active').select_related('job').prefetch_related('job__missions')
    
    if not offers.exists():
        return "Currently, there are no active job offers available."
    
    context_parts = []
    for offer in offers[:10]:  # Limit to 10 most recent offers
        missions = offer.job.missions.all()
        missions_text = ", ".join([m.description for m in missions]) if missions else "Not specified"
        
        context_parts.append(f"""
--- JOB OFFER ---
Title: {offer.title}
Location: {offer.location}
Contract Type: {offer.get_contract_type_display()}
Description: {offer.description[:300]}
Required Skills: {offer.job.required_skills}
Required Education: {offer.job.required_education}
Missions: {missions_text}
Published: {offer.published_date.strftime('%Y-%m-%d') if offer.published_date else 'N/A'}
Deadline: {offer.deadline.strftime('%Y-%m-%d') if offer.deadline else 'Open'}
""")
    
    return "\n".join(context_parts)


def get_platform_info_context():
    """RAG: Retrieve platform information for chatbot context."""
    return """
=== ALGÉRIE TÉLÉCOM RECRUITMENT PLATFORM INFORMATION ===

About Algérie Télécom:
Algérie Télécom is the leading telecommunications operator in Algeria, providing fixed-line telephony, high-speed internet, and data transmission services nationwide. As a major public company with thousands of employees, it recruits for various technical and administrative positions.

Application Process:
1. Create an account on the platform
2. Browse available job offers
3. Click "Apply" on the desired position
4. Fill in the application form with personal information
5. Upload your CV in PDF format
6. Submit your application
7. Your CV will be automatically analyzed by our AI system
8. Wait for the HR team review
9. If selected, you may receive a technical test invitation
10. Track your application status in your dashboard

Required Documents:
- CV/Resume in PDF format
- Valid email address
- Phone number
- Cover letter (optional but recommended)

Qualifications:
- Varies by position (Bachelor's, Master's, Engineering degrees)
- Technical certifications may be required for specific roles
- Professional experience as specified in each job offer

Response Time:
- Applications are reviewed within 1-2 weeks
- Technical test invitations are sent based on AI matching scores
- Final decisions are communicated within 3-4 weeks

Technical Tests:
- Multiple-choice questions (MCQ format)
- Timed tests (duration varies by position)
- Results are automatically calculated
- Minimum passing score is typically 50%

Contact:
- Use this chatbot for immediate assistance
- Visit the careers page for current openings
"""


def chatbot_response(user_message, conversation_history=None):
    """
    Generate chatbot response using Groq API + RAG.
    Retrieves relevant context from the database to provide accurate answers.
    """
    # Build RAG context
    job_offers_context = get_job_offers_context()
    platform_info = get_platform_info_context()
    
    rag_context = f"""
{platform_info}

=== CURRENT ACTIVE JOB OFFERS (Retrieved from Database) ===
{job_offers_context}
"""
    
    # System prompt for the chatbot
    system_prompt = f"""You are the "Recruitment Assistant - Algérie Télécom Carrières", an AI chatbot integrated into the Algérie Télécom recruitment platform. 

Your role is to:
1. Guide candidates through the recruitment process
2. Answer questions about available job offers
3. Provide information about application requirements
4. Help candidates understand the platform features
5. Offer tips for improving their applications

IMPORTANT RULES:
- Be friendly, professional, and helpful
- Always base your answers on the provided context (RAG data)
- If you don't know something, say so politely
- Suggest relevant job offers when appropriate
- Keep responses concise but informative
- Respond in the same language the user writes in (French or English)

CONTEXT DATA (from database):
{rag_context}"""
    
    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if available
    if conversation_history:
        for msg in conversation_history[-6:]:  # Keep last 6 messages for context
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I'm sorry, I'm having trouble processing your request right now. Please try again later. (Error: {str(e)})"
