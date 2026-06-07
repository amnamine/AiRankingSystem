"""
Seed script to populate the database with sample data for testing.
Run with: python manage.py shell < seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment_project.settings')
django.setup()

from django.contrib.auth.models import User
from recruitment.models import (
    UserProfile, Job, JobMission, JobOffer, TechnicalTest, TestQuestion
)

print("🌱 Seeding database...")

# ===== Create HR Manager =====
if not User.objects.filter(username='hr_admin').exists():
    hr_user = User.objects.create_user(
        username='hr_admin', 
        email='hr@algerietelecom.dz',
        password='hr123456',
        first_name='Fatima',
        last_name='Benali'
    )
    UserProfile.objects.create(user=hr_user, role='hr', phone='+213 555 123 456')
    print("✅ HR Manager created: hr_admin / hr123456")
else:
    hr_user = User.objects.get(username='hr_admin')
    print("ℹ️ HR Manager already exists")

# ===== Create Candidate Users =====
candidates_data = [
    ('candidate1', 'Ahmed', 'Khelifi', 'ahmed@email.com'),
    ('candidate2', 'Sara', 'Boudjema', 'sara@email.com'),
    ('candidate3', 'Mohamed', 'Taha', 'mohamed@email.com'),
]

for username, first, last, email in candidates_data:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username, email=email, password='test1234',
            first_name=first, last_name=last
        )
        UserProfile.objects.create(user=user, role='candidate')
        print(f"✅ Candidate created: {username} / test1234")

# ===== Create Jobs and Offers =====

# Job 1: Cloud Infrastructure Engineer
job1, _ = Job.objects.get_or_create(
    title="Cloud Infrastructure Engineer",
    defaults={
        'description': 'Design, implement, and manage cloud infrastructure solutions for Algérie Télécom. Ensure high availability, security, and performance of cloud-based systems.',
        'required_skills': 'AWS, Docker, Kubernetes, Terraform, Linux, Python, CI/CD, Ansible',
        'required_education': 'Master Degree in Computer Science or Engineering',
        'required_certifications': 'AWS Certified Solutions Architect, CKA',
        'category': 'IT Infrastructure',
    }
)

missions1 = [
    'Design and implement scalable cloud infrastructure on AWS',
    'Manage containerized applications using Docker and Kubernetes',
    'Implement CI/CD pipelines for automated deployments',
    'Monitor system performance and ensure 99.9% uptime',
    'Implement security best practices and compliance standards',
]
for m in missions1:
    JobMission.objects.get_or_create(job=job1, description=m)

offer1, created1 = JobOffer.objects.get_or_create(
    title="Senior Cloud Infrastructure Engineer - Algiers",
    defaults={
        'job': job1,
        'description': 'We are looking for an experienced Cloud Infrastructure Engineer to join our IT team in Algiers. You will be responsible for designing and managing our cloud-based infrastructure, ensuring high availability and security for our telecommunications services.',
        'location': 'Algiers',
        'contract_type': 'CDI',
        'status': 'active',
        'searched_profiles': '5+ years experience in cloud infrastructure, strong knowledge of AWS services, container orchestration, and DevOps practices.',
        'created_by': hr_user,
    }
)
if created1:
    print("✅ Job Offer 1 created: Senior Cloud Infrastructure Engineer")

# Job 2: Data Scientist
job2, _ = Job.objects.get_or_create(
    title="Data Scientist",
    defaults={
        'description': 'Analyze telecommunications data to extract business insights, build predictive models, and develop data-driven solutions.',
        'required_skills': 'Python, Machine Learning, TensorFlow, SQL, Pandas, NumPy, Statistics, Data Visualization',
        'required_education': 'Master or PhD in Data Science, Computer Science, or Statistics',
        'required_certifications': 'Google Data Analytics, TensorFlow Developer Certificate',
        'category': 'Data & AI',
    }
)

missions2 = [
    'Develop and deploy machine learning models for network optimization',
    'Analyze customer behavior patterns using statistical methods',
    'Build data pipelines for real-time analytics',
    'Create dashboards and reports for business stakeholders',
    'Research and implement new AI/ML techniques',
]
for m in missions2:
    JobMission.objects.get_or_create(job=job2, description=m)

offer2, created2 = JobOffer.objects.get_or_create(
    title="Data Scientist - AI & Analytics Team",
    defaults={
        'job': job2,
        'description': 'Join our growing AI & Analytics team to leverage data-driven insights for improving our telecommunications services. Work on cutting-edge machine learning projects.',
        'location': 'Blida',
        'contract_type': 'CDI',
        'status': 'active',
        'searched_profiles': '3+ years experience in data science, proficiency in Python and ML frameworks.',
        'created_by': hr_user,
    }
)
if created2:
    print("✅ Job Offer 2 created: Data Scientist")

# Job 3: Cybersecurity Analyst
job3, _ = Job.objects.get_or_create(
    title="Cybersecurity Analyst",
    defaults={
        'description': 'Protect Algérie Télécom network infrastructure and data from cyber threats. Implement security measures and monitor for vulnerabilities.',
        'required_skills': 'Network Security, SIEM, Firewall, Penetration Testing, Python, Incident Response, Risk Assessment',
        'required_education': 'Bachelor or Master Degree in Cybersecurity or Computer Science',
        'required_certifications': 'CCSP, CEH, AZ-500',
        'category': 'Cybersecurity',
    }
)

missions3 = [
    'Monitor and analyze security alerts from SIEM systems',
    'Conduct penetration testing and vulnerability assessments',
    'Implement and maintain firewall and intrusion detection systems',
    'Respond to and investigate security incidents',
    'Develop security policies and procedures',
]
for m in missions3:
    JobMission.objects.get_or_create(job=job3, description=m)

offer3, created3 = JobOffer.objects.get_or_create(
    title="Cybersecurity Analyst - Network Security",
    defaults={
        'job': job3,
        'description': 'We are seeking a skilled Cybersecurity Analyst to strengthen our network security operations. Protect critical telecommunications infrastructure against evolving cyber threats.',
        'location': 'Oran',
        'contract_type': 'CDI',
        'status': 'active',
        'searched_profiles': '2+ years experience in cybersecurity, knowledge of SIEM tools and network security.',
        'created_by': hr_user,
    }
)
if created3:
    print("✅ Job Offer 3 created: Cybersecurity Analyst")

# Job 4: Full-Stack Web Developer (Internship)
job4, _ = Job.objects.get_or_create(
    title="Full-Stack Web Developer",
    defaults={
        'description': 'Develop and maintain web applications for internal and customer-facing platforms. Work with modern JavaScript and Python frameworks.',
        'required_skills': 'JavaScript, React, Django, Python, HTML, CSS, PostgreSQL, Git',
        'required_education': 'Bachelor Degree in Computer Science or Software Engineering',
        'required_certifications': '',
        'category': 'Software Development',
    }
)

missions4 = [
    'Develop responsive front-end interfaces using React',
    'Build and maintain REST APIs with Django',
    'Collaborate with UI/UX designers for optimal user experience',
    'Write unit tests and integration tests',
    'Participate in agile development sprints',
]
for m in missions4:
    JobMission.objects.get_or_create(job=job4, description=m)

offer4, created4 = JobOffer.objects.get_or_create(
    title="Full-Stack Developer Internship - Web Platform",
    defaults={
        'job': job4,
        'description': 'An exciting 6-month internship opportunity to work on Algérie Télécom web platforms. Gain hands-on experience with modern web technologies in a professional environment.',
        'location': 'Algiers',
        'contract_type': 'Stage',
        'status': 'active',
        'searched_profiles': 'Computer Science student or recent graduate with knowledge of web development.',
        'created_by': hr_user,
    }
)
if created4:
    print("✅ Job Offer 4 created: Full-Stack Developer Internship")

# Job 5: Network Engineer
job5, _ = Job.objects.get_or_create(
    title="Network Engineer",
    defaults={
        'description': 'Design, configure, and maintain Algérie Télécom telecommunications network infrastructure including fiber optic, MPLS, and IP networks.',
        'required_skills': 'Cisco, MPLS, BGP, OSPF, Fiber Optics, Network Monitoring, VPN, TCP/IP',
        'required_education': 'Engineering Degree in Telecommunications or Computer Networks',
        'required_certifications': 'CCNA, CCNP',
        'category': 'Telecommunications',
    }
)

missions5 = [
    'Configure and maintain core network routers and switches',
    'Design and implement network expansion projects',
    'Troubleshoot and resolve network connectivity issues',
    'Monitor network performance and implement optimizations',
    'Plan and execute network migrations and upgrades',
]
for m in missions5:
    JobMission.objects.get_or_create(job=job5, description=m)

offer5, created5 = JobOffer.objects.get_or_create(
    title="Network Engineer - Telecommunications Core",
    defaults={
        'job': job5,
        'description': 'Join our telecommunications team to manage and expand Algeria core network infrastructure. Work with cutting-edge fiber optic and IP networking technologies.',
        'location': 'Constantine',
        'contract_type': 'CDI',
        'status': 'active',
        'searched_profiles': '3+ years experience in telecommunications networking, CCNP certified.',
        'created_by': hr_user,
    }
)
if created5:
    print("✅ Job Offer 5 created: Network Engineer")


# ===== Create Technical Tests =====

# Test for Cloud Engineer
if created1:
    test1 = TechnicalTest.objects.create(
        job_offer=offer1,
        title="Cloud Infrastructure Assessment",
        duration_minutes=30,
        passing_score=50,
    )
    
    questions_data = [
        {
            'text': 'Which AWS service is used for container orchestration?',
            'a': 'AWS Lambda', 'b': 'Amazon ECS/EKS', 'c': 'Amazon S3', 'd': 'Amazon RDS',
            'correct': 'B'
        },
        {
            'text': 'What does Terraform primarily do?',
            'a': 'Application monitoring', 'b': 'Database management', 'c': 'Infrastructure as Code provisioning', 'd': 'Code compilation',
            'correct': 'C'
        },
        {
            'text': 'In Kubernetes, what is a Pod?',
            'a': 'A network policy', 'b': 'A storage volume', 'c': 'The smallest deployable unit that can run containers', 'd': 'A load balancer',
            'correct': 'C'
        },
        {
            'text': 'Which Docker command builds an image from a Dockerfile?',
            'a': 'docker run', 'b': 'docker pull', 'c': 'docker build', 'd': 'docker push',
            'correct': 'C'
        },
        {
            'text': 'What is the purpose of a CI/CD pipeline?',
            'a': 'Manual code deployment', 'b': 'Automated building, testing, and deployment of code', 'c': 'Database backup', 'd': 'Network monitoring',
            'correct': 'B'
        },
    ]
    
    for q in questions_data:
        TestQuestion.objects.create(
            test=test1,
            question_text=q['text'],
            option_a=q['a'], option_b=q['b'],
            option_c=q['c'], option_d=q['d'],
            correct_answer=q['correct'],
        )
    print("✅ Technical test created for Cloud Engineer (5 questions)")

# Test for Data Scientist
if created2:
    test2 = TechnicalTest.objects.create(
        job_offer=offer2,
        title="Data Science & Machine Learning Assessment",
        duration_minutes=25,
        passing_score=50,
    )
    
    ds_questions = [
        {
            'text': 'What is the purpose of a training/test split in machine learning?',
            'a': 'To reduce dataset size', 'b': 'To evaluate model performance on unseen data', 'c': 'To speed up training', 'd': 'To remove outliers',
            'correct': 'B'
        },
        {
            'text': 'Which Python library is commonly used for deep learning?',
            'a': 'Pandas', 'b': 'Matplotlib', 'c': 'TensorFlow', 'd': 'BeautifulSoup',
            'correct': 'C'
        },
        {
            'text': 'What does overfitting mean in machine learning?',
            'a': 'The model performs well on both training and test data', 'b': 'The model performs poorly on training data', 'c': 'The model memorizes training data but fails on new data', 'd': 'The model has too few parameters',
            'correct': 'C'
        },
        {
            'text': 'Which metric is best for imbalanced classification problems?',
            'a': 'Accuracy', 'b': 'F1 Score', 'c': 'Mean Squared Error', 'd': 'R-squared',
            'correct': 'B'
        },
    ]
    
    for q in ds_questions:
        TestQuestion.objects.create(
            test=test2,
            question_text=q['text'],
            option_a=q['a'], option_b=q['b'],
            option_c=q['c'], option_d=q['d'],
            correct_answer=q['correct'],
        )
    print("✅ Technical test created for Data Scientist (4 questions)")

# Test for Cybersecurity
if created3:
    test3 = TechnicalTest.objects.create(
        job_offer=offer3,
        title="Cybersecurity Fundamentals Assessment",
        duration_minutes=20,
        passing_score=50,
    )
    
    sec_questions = [
        {
            'text': 'What is a SIEM system used for?',
            'a': 'Web development', 'b': 'Security information and event management', 'c': 'Database optimization', 'd': 'Email marketing',
            'correct': 'B'
        },
        {
            'text': 'What type of attack sends excessive traffic to overwhelm a target?',
            'a': 'Phishing', 'b': 'SQL Injection', 'c': 'DDoS', 'd': 'Cross-Site Scripting',
            'correct': 'C'
        },
        {
            'text': 'What does a firewall primarily do?',
            'a': 'Encrypt data at rest', 'b': 'Filter network traffic based on rules', 'c': 'Compress data packets', 'd': 'Store log files',
            'correct': 'B'
        },
    ]
    
    for q in sec_questions:
        TestQuestion.objects.create(
            test=test3,
            question_text=q['text'],
            option_a=q['a'], option_b=q['b'],
            option_c=q['c'], option_d=q['d'],
            correct_answer=q['correct'],
        )
    print("✅ Technical test created for Cybersecurity (3 questions)")

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@algerietelecom.dz', 'admin123')
    print("✅ Superuser created: admin / admin123")

print("\n🎉 Database seeding complete!")
print("\n📋 Login Credentials:")
print("   HR Manager:  hr_admin / hr123456")
print("   Candidate 1: candidate1 / test1234")
print("   Candidate 2: candidate2 / test1234")
print("   Candidate 3: candidate3 / test1234")
print("   Admin:       admin / admin123")
