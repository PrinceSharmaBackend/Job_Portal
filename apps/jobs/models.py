from django.db import models
from django.conf import settings


class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'categories'
        ordering  = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Job(models.Model):
    class JobType(models.TextChoices):
        FULL_TIME  = 'full_time',  'Full Time'
        PART_TIME  = 'part_time',  'Part Time'
        CONTRACT   = 'contract',   'Contract'
        INTERNSHIP = 'internship', 'Internship'
        REMOTE     = 'remote',     'Remote'
        FREELANCE  = 'freelance',  'Freelance'

    class ExperienceLevel(models.TextChoices):
        ENTRY  = 'entry',  'Entry Level'
        MID    = 'mid',    'Mid Level'
        SENIOR = 'senior', 'Senior Level'
        LEAD   = 'lead',   'Lead / Manager'

    class Status(models.TextChoices):
        DRAFT    = 'draft',    'Draft'
        ACTIVE   = 'active',   'Active'
        CLOSED   = 'closed',   'Closed'
        PAUSED   = 'paused',   'Paused'

    # Relationships
    employer  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_jobs',
        limit_choices_to={'role': 'employer'},
    )
    category  = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')

    # Basic info
    title            = models.CharField(max_length=200)
    company_name     = models.CharField(max_length=200)
    company_logo     = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description      = models.TextField()
    requirements     = models.TextField()
    responsibilities = models.TextField(blank=True)
    benefits         = models.TextField(blank=True)

    # Details
    job_type         = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FULL_TIME)
    experience_level = models.CharField(max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY)
    location         = models.CharField(max_length=200)
    is_remote        = models.BooleanField(default=False)
    skills_required  = models.TextField(help_text='Comma-separated skills')

    # Salary
    salary_min       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency  = models.CharField(max_length=10, default='INR')

    # Status & dates
    status           = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    deadline         = models.DateField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    # Stats
    views_count      = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} @ {self.company_name}"

    @property
    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
        return "Not disclosed"

    @property
    def total_applications(self):
        return self.applications.count()


class Application(models.Model):
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        REVIEWING  = 'reviewing',  'Reviewing'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        REJECTED   = 'rejected',  'Rejected'
        HIRED      = 'hired',     'Hired'

    job        = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    cover_letter = models.TextField(blank=True)
    resume       = models.FileField(upload_to='application_resumes/', blank=True, null=True)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    applied_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    notes        = models.TextField(blank=True, help_text='Employer notes — not visible to applicant')

    class Meta:
        db_table = 'applications'
        ordering = ['-applied_at']
        # One user can only apply once per job
        unique_together = ['job', 'applicant']

    def __str__(self):
        return f"{self.applicant.get_full_name()} → {self.job.title}"


class SavedJob(models.Model):
    user     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_jobs')
    job      = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_jobs'
        unique_together = ['user', 'job']
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.email} saved {self.job.title}"
