from django.contrib import admin
from .models import (
    UserProfile, Job, JobMission, JobOffer, TechnicalTest,
    TestQuestion, Application, TestAssignment, TestAnswer, ChatMessage
)


class JobMissionInline(admin.TabularInline):
    model = JobMission
    extra = 1


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 1


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at')
    list_filter = ('role',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')
    inlines = [JobMissionInline]


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'contract_type', 'status', 'published_date')
    list_filter = ('status', 'contract_type')


@admin.register(TechnicalTest)
class TechnicalTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'job_offer', 'duration_minutes', 'passing_score')
    inlines = [TestQuestionInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job_offer', 'status', 'ai_score', 'applied_at')
    list_filter = ('status',)


@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('application', 'status', 'score', 'assigned_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
