from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile for role management."""
    ROLE_CHOICES = [
        ('candidate', 'Candidate'),
        ('hr', 'HR Manager'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='candidate')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Job(models.Model):
    """Job category / domain."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.TextField(help_text="Comma-separated list of required skills")
    required_education = models.CharField(max_length=200, blank=True)
    required_certifications = models.TextField(blank=True, help_text="Comma-separated certifications")
    category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title


class JobMission(models.Model):
    """Missions/responsibilities for a job."""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='missions')
    description = models.TextField()

    def __str__(self):
        return f"Mission for {self.job.title}: {self.description[:50]}"


class JobOffer(models.Model):
    """Published job offer."""
    CONTRACT_CHOICES = [
        ('CDI', 'CDI - Permanent'),
        ('CDD', 'CDD - Fixed-term'),
        ('Stage', 'Internship'),
        ('Freelance', 'Freelance'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    ]
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    contract_type = models.CharField(max_length=20, choices=CONTRACT_CHOICES, default='CDI')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    published_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_offers')
    searched_profiles = models.TextField(blank=True, help_text="Description of ideal candidate profiles")

    def __str__(self):
        return f"{self.title} - {self.location}"


class TechnicalTest(models.Model):
    """Technical test linked to a job offer."""
    job_offer = models.OneToOneField(JobOffer, on_delete=models.CASCADE, related_name='test')
    title = models.CharField(max_length=200)
    duration_minutes = models.IntegerField(default=30)
    passing_score = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test: {self.title}"


class TestQuestion(models.Model):
    """MCQ question for a technical test."""
    test = models.ForeignKey(TechnicalTest, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

    def __str__(self):
        return self.question_text[:80]


class Application(models.Model):
    """Candidate application for a job offer."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('test_sent', 'Test Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name='applications')
    cv_file = models.FileField(upload_to='cvs/')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    # AI Matching Fields
    ai_score = models.FloatField(null=True, blank=True)
    ai_profile_score = models.FloatField(null=True, blank=True)
    ai_semantic_score = models.FloatField(null=True, blank=True)
    ai_mission_score = models.FloatField(null=True, blank=True)
    ai_category_score = models.FloatField(null=True, blank=True)
    ai_quality_score = models.FloatField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)
    ai_matched_skills = models.TextField(blank=True)
    ai_matched_missions = models.TextField(blank=True)
    ai_strengths = models.TextField(blank=True)
    ai_weaknesses = models.TextField(blank=True)
    resume_text = models.TextField(blank=True)

    class Meta:
        unique_together = ['candidate', 'job_offer']
        ordering = ['-ai_score']

    def __str__(self):
        return f"{self.candidate.username} -> {self.job_offer.title} (Score: {self.ai_score})"


class TestAssignment(models.Model):
    """Links a candidate to a technical test."""
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='test_assignment')
    test = models.ForeignKey(TechnicalTest, on_delete=models.CASCADE, related_name='assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    score = models.FloatField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Test for {self.application.candidate.username}"


class TestAnswer(models.Model):
    """Individual answer submitted by a candidate."""
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer by {self.assignment.application.candidate.username}"


class ChatMessage(models.Model):
    """Chatbot conversation messages."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages', null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat: {self.message[:50]}"
