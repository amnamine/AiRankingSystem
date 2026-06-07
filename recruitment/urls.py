from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.home_page, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Job Offers
    path('offers/', views.job_offers_list, name='job_offers'),
    path('offers/<int:offer_id>/', views.job_offer_detail, name='job_offer_detail'),
    
    # Applications
    path('apply/<int:offer_id>/', views.apply_job, name='apply_job'),
    
    # Candidate Dashboard
    path('dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    
    # Technical Tests
    path('test/<int:assignment_id>/', views.take_test, name='take_test'),
    
    # HR Dashboard
    path('hr/', views.hr_dashboard, name='hr_dashboard'),
    path('hr/create-offer/', views.hr_create_offer, name='hr_create_offer'),
    path('hr/application/<int:app_id>/', views.hr_application_detail, name='hr_application_detail'),
    path('hr/send-test/<int:app_id>/', views.hr_send_test, name='hr_send_test'),
    path('hr/update-status/<int:app_id>/', views.hr_update_status, name='hr_update_status'),
    
    # Chatbot API
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
]
