from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.jobs.models import Category, Job, Application, SavedJob


def create_user(email, role='job_seeker', password='StrongPass@123'):
    return User.objects.create_user(
        email=email, password=password,
        first_name='Test', last_name='User', role=role,
    )


def get_tokens(client, email, password='StrongPass@123'):
    res = client.post(reverse('auth-login'), {'email': email, 'password': password}, format='json')
    return res.data['access']


def create_category():
    return Category.objects.create(name='Tech', slug='tech')


def create_job(employer, category, status=Job.Status.ACTIVE):
    return Job.objects.create(
        employer=employer,
        category=category,
        title='Backend Developer',
        company_name='TechCorp',
        description='Build APIs',
        requirements='Python, Django',
        job_type=Job.JobType.FULL_TIME,
        experience_level=Job.ExperienceLevel.ENTRY,
        location='Mumbai',
        skills_required='Python, Django, PostgreSQL',
        status=status,
    )


# ─── Job List & Detail ────────────────────────────────────────────────────────

class JobListTestCase(APITestCase):
    def setUp(self):
        self.employer = create_user('emp@example.com', role='employer')
        self.category = create_category()
        self.job = create_job(self.employer, self.category)

    def test_list_active_jobs_public(self):
        res = self.client.get(reverse('job-list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

    def test_draft_job_not_in_public_list(self):
        create_job(self.employer, self.category, status=Job.Status.DRAFT)
        res = self.client.get(reverse('job-list'))
        self.assertEqual(res.data['count'], 1)  # only active job

    def test_search_by_title(self):
        res = self.client.get(reverse('job-list'), {'search': 'Backend'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

    def test_filter_by_job_type(self):
        res = self.client.get(reverse('job-list'), {'job_type': 'full_time'})
        self.assertEqual(res.data['count'], 1)

    def test_job_detail_public(self):
        res = self.client.get(reverse('job-detail', args=[self.job.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['title'], 'Backend Developer')

    def test_job_detail_increments_views(self):
        self.client.get(reverse('job-detail', args=[self.job.pk]))
        self.job.refresh_from_db()
        self.assertEqual(self.job.views_count, 1)


# ─── Employer Job CRUD ────────────────────────────────────────────────────────

class EmployerJobCRUDTestCase(APITestCase):
    def setUp(self):
        self.employer = create_user('emp@example.com', role='employer')
        self.seeker = create_user('seeker@example.com', role='job_seeker')
        self.category = create_category()
        token = get_tokens(self.client, 'emp@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def get_job_payload(self):
        return {
            'title': 'Django Developer',
            'company_name': 'StartupX',
            'description': 'Build backend',
            'requirements': 'Python, Django',
            'job_type': 'full_time',
            'experience_level': 'entry',
            'location': 'Remote',
            'skills_required': 'Django, REST',
            'status': 'active',
        }

    def test_employer_can_create_job(self):
        res = self.client.post(reverse('employer-jobs'), self.get_job_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.count(), 1)

    def test_employer_can_list_own_jobs(self):
        create_job(self.employer, self.category)
        res = self.client.get(reverse('employer-jobs'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

    def test_employer_can_update_job(self):
        job = create_job(self.employer, self.category)
        res = self.client.patch(
            reverse('employer-job-detail', args=[job.pk]),
            {'title': 'Senior Django Dev'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_employer_can_delete_job(self):
        job = create_job(self.employer, self.category)
        res = self.client.delete(reverse('employer-job-detail', args=[job.pk]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Job.objects.count(), 0)

    def test_job_seeker_cannot_create_job(self):
        token = get_tokens(self.client, 'seeker@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.post(reverse('employer-jobs'), self.get_job_payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_employer_cannot_edit_others_job(self):
        other_emp = create_user('other@example.com', role='employer')
        job = create_job(other_emp, self.category)
        res = self.client.patch(
            reverse('employer-job-detail', args=[job.pk]),
            {'title': 'Hacked'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


# ─── Applications ─────────────────────────────────────────────────────────────

class ApplicationTestCase(APITestCase):
    def setUp(self):
        self.employer = create_user('emp@example.com', role='employer')
        self.seeker = create_user('seeker@example.com', role='job_seeker')
        self.category = create_category()
        self.job = create_job(self.employer, self.category)
        token = get_tokens(self.client, 'seeker@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_seeker_can_apply(self):
        res = self.client.post(reverse('apply-job'), {
            'job': self.job.pk,
            'cover_letter': 'I am a great fit!',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)

    def test_seeker_cannot_apply_twice(self):
        self.client.post(reverse('apply-job'), {'job': self.job.pk}, format='json')
        res = self.client.post(reverse('apply-job'), {'job': self.job.pk}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_seeker_cannot_apply_to_closed_job(self):
        closed_job = create_job(self.employer, self.category, status=Job.Status.CLOSED)
        res = self.client.post(reverse('apply-job'), {'job': closed_job.pk}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_seeker_can_view_own_applications(self):
        Application.objects.create(job=self.job, applicant=self.seeker)
        res = self.client.get(reverse('my-applications'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

    def test_seeker_can_withdraw_pending_application(self):
        app = Application.objects.create(job=self.job, applicant=self.seeker)
        res = self.client.delete(reverse('withdraw-application', args=[app.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(Application.objects.count(), 0)

    def test_employer_can_view_job_applications(self):
        Application.objects.create(job=self.job, applicant=self.seeker)
        token = get_tokens(self.client, 'emp@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get(reverse('job-applications', args=[self.job.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)

    def test_employer_can_update_application_status(self):
        app = Application.objects.create(job=self.job, applicant=self.seeker)
        token = get_tokens(self.client, 'emp@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.patch(
            reverse('update-application-status', args=[app.pk]),
            {'status': 'shortlisted'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, 'shortlisted')


# ─── Saved Jobs ───────────────────────────────────────────────────────────────

class SavedJobTestCase(APITestCase):
    def setUp(self):
        self.employer = create_user('emp@example.com', role='employer')
        self.seeker = create_user('seeker@example.com', role='job_seeker')
        self.category = create_category()
        self.job = create_job(self.employer, self.category)
        token = get_tokens(self.client, 'seeker@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_seeker_can_save_job(self):
        res = self.client.post(reverse('save-job', args=[self.job.pk]))
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['saved'])

    def test_seeker_can_unsave_job(self):
        SavedJob.objects.create(user=self.seeker, job=self.job)
        res = self.client.post(reverse('save-job', args=[self.job.pk]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['saved'])

    def test_seeker_can_list_saved_jobs(self):
        SavedJob.objects.create(user=self.seeker, job=self.job)
        res = self.client.get(reverse('saved-jobs'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 1)


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardTestCase(APITestCase):
    def setUp(self):
        self.employer = create_user('emp@example.com', role='employer')
        self.seeker = create_user('seeker@example.com', role='job_seeker')

    def test_employer_dashboard(self):
        token = get_tokens(self.client, 'emp@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get(reverse('employer-dashboard'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_jobs', res.data)

    def test_seeker_dashboard(self):
        token = get_tokens(self.client, 'seeker@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get(reverse('seeker-dashboard'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_applications', res.data)

    def test_employer_cannot_access_seeker_dashboard(self):
        token = get_tokens(self.client, 'emp@example.com')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get(reverse('seeker-dashboard'))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
