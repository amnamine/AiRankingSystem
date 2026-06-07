import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg, Count

from .models import (
    UserProfile, Job, JobMission, JobOffer, TechnicalTest, 
    TestQuestion, Application, TestAssignment, TestAnswer, ChatMessage
)
from .ai_matching import analyze_resume, generate_ai_summary
from .chatbot import chatbot_response


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

def home_page(request):
    """Landing page with job categories and platform info."""
    categories = Job.objects.values_list('category', flat=True).distinct()
    active_offers_count = JobOffer.objects.filter(status='active').count()
    context = {
        'categories': [c for c in categories if c],
        'active_offers_count': active_offers_count,
    }
    return render(request, 'home.html', context)


def register_view(request):
    """User registration for candidates and HR managers."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'candidate')
        phone = request.POST.get('phone', '')
        
        if password != password2:
            return render(request, 'register.html', {'error': 'Passwords do not match'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already registered'})
        
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        UserProfile.objects.create(user=user, role=role, phone=phone)
        
        login(request, user)
        if role == 'hr':
            return redirect('hr_dashboard')
        return redirect('candidate_dashboard')
    
    return render(request, 'register.html')


def login_view(request):
    """User login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            profile = getattr(user, 'profile', None)
            if profile and profile.role == 'hr':
                return redirect('hr_dashboard')
            return redirect('candidate_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')


def logout_view(request):
    """User logout."""
    logout(request)
    return redirect('home')


# ============================================================
# JOB OFFERS VIEWS
# ============================================================

def job_offers_list(request):
    """Display all active job offers with filters."""
    offers = JobOffer.objects.filter(status='active').select_related('job').order_by('-published_date')
    
    # Filters
    contract_type = request.GET.get('contract_type')
    location = request.GET.get('location')
    category = request.GET.get('category')
    
    if contract_type:
        offers = offers.filter(contract_type=contract_type)
    if location:
        offers = offers.filter(location__icontains=location)
    if category:
        offers = offers.filter(job__category__icontains=category)
    
    locations = JobOffer.objects.filter(status='active').values_list('location', flat=True).distinct()
    categories = Job.objects.values_list('category', flat=True).distinct()
    
    context = {
        'offers': offers,
        'locations': locations,
        'categories': [c for c in categories if c],
        'current_contract': contract_type,
        'current_location': location,
        'current_category': category,
    }
    return render(request, 'job_offers.html', context)


def job_offer_detail(request, offer_id):
    """Display job offer details."""
    offer = get_object_or_404(JobOffer, id=offer_id)
    missions = offer.job.missions.all()
    has_applied = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(
            candidate=request.user, job_offer=offer
        ).exists()
    
    context = {
        'offer': offer,
        'missions': missions,
        'has_applied': has_applied,
    }
    return render(request, 'job_offer_detail.html', context)


# ============================================================
# APPLICATION VIEWS
# ============================================================

@login_required
def apply_job(request, offer_id):
    """Submit job application with CV."""
    offer = get_object_or_404(JobOffer, id=offer_id, status='active')
    
    # Check if already applied
    if Application.objects.filter(candidate=request.user, job_offer=offer).exists():
        return render(request, 'apply.html', {
            'offer': offer,
            'error': 'You have already applied for this offer.'
        })
    
    if request.method == 'POST':
        cv_file = request.FILES.get('cv_file')
        cover_letter = request.POST.get('cover_letter', '')
        
        if not cv_file:
            return render(request, 'apply.html', {
                'offer': offer,
                'error': 'Please upload your CV in PDF format.'
            })
        
        if not cv_file.name.endswith('.pdf'):
            return render(request, 'apply.html', {
                'offer': offer,
                'error': 'Only PDF files are accepted.'
            })
        
        # Create application
        application = Application.objects.create(
            candidate=request.user,
            job_offer=offer,
            cv_file=cv_file,
            cover_letter=cover_letter,
            status='pending'
        )
        
        # Run AI analysis
        try:
            results = analyze_resume(application.cv_file.path, offer)
            
            application.ai_score = results.get('final_score', 0)
            application.ai_profile_score = results.get('profile_score', 0)
            application.ai_semantic_score = results.get('semantic_score', 0)
            application.ai_mission_score = results.get('mission_score', 0)
            application.ai_category_score = results.get('category_score', 0)
            application.ai_quality_score = results.get('quality_score', 0)
            application.ai_matched_skills = json.dumps(results.get('matched_skills', []))
            application.ai_matched_missions = json.dumps(results.get('matched_missions', []))
            application.ai_strengths = json.dumps(results.get('strengths', []))
            application.ai_weaknesses = json.dumps(results.get('weaknesses', []))
            application.resume_text = results.get('resume_text', '')
            
            # Generate AI Summary
            summary = generate_ai_summary(
                results.get('resume_text', ''), offer, results
            )
            application.ai_summary = summary
            application.save()
            
        except Exception as e:
            print(f"AI analysis error: {e}")
            application.ai_summary = f"AI analysis failed: {str(e)}"
            application.save()
        
        return redirect('candidate_dashboard')
    
    return render(request, 'apply.html', {'offer': offer})


# ============================================================
# CANDIDATE DASHBOARD
# ============================================================

@login_required
def candidate_dashboard(request):
    """Candidate dashboard showing application status."""
    applications = Application.objects.filter(
        candidate=request.user
    ).select_related('job_offer', 'job_offer__job').order_by('-applied_at')
    
    # Check for test assignments
    for app in applications:
        try:
            app.test_info = app.test_assignment
        except TestAssignment.DoesNotExist:
            app.test_info = None
    
    context = {
        'applications': applications,
        'total_applications': applications.count(),
        'pending_count': applications.filter(status='pending').count(),
        'accepted_count': applications.filter(status='accepted').count(),
        'rejected_count': applications.filter(status='rejected').count(),
    }
    return render(request, 'candidate_dashboard.html', context)


# ============================================================
# TECHNICAL TEST VIEWS
# ============================================================

@login_required
def take_test(request, assignment_id):
    """Candidate takes a technical test."""
    assignment = get_object_or_404(
        TestAssignment, id=assignment_id, 
        application__candidate=request.user
    )
    
    if assignment.status == 'completed':
        return render(request, 'test_result.html', {'assignment': assignment})
    
    test = assignment.test
    questions = test.questions.all()
    
    if request.method == 'POST':
        correct = 0
        total = questions.count()
        
        for question in questions:
            selected = request.POST.get(f'question_{question.id}')
            is_correct = selected == question.correct_answer
            if is_correct:
                correct += 1
            
            TestAnswer.objects.create(
                assignment=assignment,
                question=question,
                selected_answer=selected or '',
                is_correct=is_correct
            )
        
        score = (correct / total * 100) if total > 0 else 0
        assignment.score = score
        assignment.status = 'completed'
        assignment.completed_at = timezone.now()
        assignment.save()
        
        return render(request, 'test_result.html', {
            'assignment': assignment,
            'correct': correct,
            'total': total,
        })
    
    # Mark as in progress
    assignment.status = 'in_progress'
    assignment.save()
    
    context = {
        'assignment': assignment,
        'test': test,
        'questions': questions,
    }
    return render(request, 'take_test.html', context)


# ============================================================
# HR DASHBOARD VIEWS
# ============================================================

@login_required
def hr_dashboard(request):
    """HR Manager dashboard with all applications and statistics."""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'hr':
        return redirect('candidate_dashboard')
    
    offers = JobOffer.objects.all().order_by('-published_date')
    
    selected_offer_id = request.GET.get('offer_id')
    applications = None
    selected_offer = None
    
    if selected_offer_id:
        selected_offer = get_object_or_404(JobOffer, id=selected_offer_id)
        applications = Application.objects.filter(
            job_offer=selected_offer
        ).select_related('candidate').order_by('-ai_score')
    
    # Statistics
    total_applications = Application.objects.count()
    avg_score = Application.objects.aggregate(avg=Avg('ai_score'))['avg'] or 0
    
    context = {
        'offers': offers,
        'applications': applications,
        'selected_offer': selected_offer,
        'total_applications': total_applications,
        'avg_score': round(avg_score, 1),
        'active_offers': offers.filter(status='active').count(),
    }
    return render(request, 'hr_dashboard.html', context)


@login_required
def hr_create_offer(request):
    """HR creates a new job offer."""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'hr':
        return redirect('home')
    
    if request.method == 'POST':
        # Create Job first
        job = Job.objects.create(
            title=request.POST.get('job_title'),
            description=request.POST.get('job_description'),
            required_skills=request.POST.get('required_skills'),
            required_education=request.POST.get('required_education', ''),
            required_certifications=request.POST.get('required_certifications', ''),
            category=request.POST.get('category', ''),
        )
        
        # Create missions
        missions = request.POST.getlist('missions')
        for mission in missions:
            if mission.strip():
                JobMission.objects.create(job=job, description=mission.strip())
        
        # Create Job Offer
        offer = JobOffer.objects.create(
            job=job,
            title=request.POST.get('offer_title'),
            description=request.POST.get('offer_description'),
            location=request.POST.get('location'),
            contract_type=request.POST.get('contract_type', 'CDI'),
            searched_profiles=request.POST.get('searched_profiles', ''),
            created_by=request.user,
        )
        
        deadline = request.POST.get('deadline')
        if deadline:
            offer.deadline = deadline
            offer.save()
        
        # Create technical test if provided
        test_title = request.POST.get('test_title')
        if test_title:
            test = TechnicalTest.objects.create(
                job_offer=offer,
                title=test_title,
                duration_minutes=int(request.POST.get('test_duration', 30)),
                passing_score=int(request.POST.get('passing_score', 50)),
            )
            
            # Add questions
            q_idx = 1
            while request.POST.get(f'q_{q_idx}_text'):
                TestQuestion.objects.create(
                    test=test,
                    question_text=request.POST.get(f'q_{q_idx}_text'),
                    option_a=request.POST.get(f'q_{q_idx}_a', ''),
                    option_b=request.POST.get(f'q_{q_idx}_b', ''),
                    option_c=request.POST.get(f'q_{q_idx}_c', ''),
                    option_d=request.POST.get(f'q_{q_idx}_d', ''),
                    correct_answer=request.POST.get(f'q_{q_idx}_correct', 'A'),
                )
                q_idx += 1
        
        return redirect('hr_dashboard')
    
    return render(request, 'hr_create_offer.html')


@login_required
def hr_application_detail(request, app_id):
    """HR views detailed application with AI analysis."""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'hr':
        return redirect('home')
    
    application = get_object_or_404(Application, id=app_id)
    
    # Parse JSON fields
    try:
        matched_skills = json.loads(application.ai_matched_skills) if application.ai_matched_skills else []
    except:
        matched_skills = []
    
    try:
        matched_missions = json.loads(application.ai_matched_missions) if application.ai_matched_missions else []
    except:
        matched_missions = []
    
    try:
        strengths = json.loads(application.ai_strengths) if application.ai_strengths else []
    except:
        strengths = []
    
    try:
        weaknesses = json.loads(application.ai_weaknesses) if application.ai_weaknesses else []
    except:
        weaknesses = []
    
    # Check test availability
    has_test = hasattr(application.job_offer, 'test')
    test_sent = hasattr(application, 'test_assignment')
    can_send_test = (
        has_test and 
        not test_sent and 
        application.ai_score is not None and 
        application.ai_score >= 50
    )
    
    context = {
        'application': application,
        'matched_skills': matched_skills,
        'matched_missions': matched_missions,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'has_test': has_test,
        'test_sent': test_sent,
        'can_send_test': can_send_test,
    }
    return render(request, 'hr_application_detail.html', context)


@login_required
@require_POST
def hr_send_test(request, app_id):
    """HR sends technical test to candidate."""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'hr':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    application = get_object_or_404(Application, id=app_id)
    
    if not hasattr(application.job_offer, 'test'):
        return JsonResponse({'error': 'No test linked to this job offer'}, status=400)
    
    if hasattr(application, 'test_assignment'):
        return JsonResponse({'error': 'Test already sent to this candidate'}, status=400)
    
    if application.ai_score is not None and application.ai_score < 50:
        return JsonResponse({'error': 'AI score below threshold (50%)'}, status=400)
    
    test = application.job_offer.test
    if not test.questions.exists():
        return JsonResponse({'error': 'No questions in test'}, status=400)
    
    TestAssignment.objects.create(
        application=application,
        test=test,
        status='sent'
    )
    
    application.status = 'test_sent'
    application.save()
    
    return JsonResponse({'success': True, 'message': 'Test sent successfully'})


@login_required
@require_POST
def hr_update_status(request, app_id):
    """HR updates application status."""
    profile = getattr(request.user, 'profile', None)
    if not profile or profile.role != 'hr':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    application = get_object_or_404(Application, id=app_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Application.STATUS_CHOICES):
        application.status = new_status
        application.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid status'}, status=400)


# ============================================================
# CHATBOT API
# ============================================================

@csrf_exempt
def chatbot_api(request):
    """API endpoint for chatbot interactions."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            history = data.get('history', [])
            
            if not message:
                return JsonResponse({'error': 'Empty message'}, status=400)
            
            response = chatbot_response(message, history)
            
            # Save chat message if user is authenticated
            if request.user.is_authenticated:
                ChatMessage.objects.create(
                    user=request.user,
                    message=message,
                    response=response,
                )
            
            return JsonResponse({
                'response': response,
                'status': 'success'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST only'}, status=405)
