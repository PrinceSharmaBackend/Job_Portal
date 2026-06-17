from rest_framework import serializers
from .models import Category, Job, Application, SavedJob
from apps.accounts.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(source='jobs.count', read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'description', 'job_count']


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job listing."""
    category         = CategorySerializer(read_only=True)
    salary_range     = serializers.ReadOnlyField()
    total_applications = serializers.ReadOnlyField()
    employer_name    = serializers.CharField(source='employer.get_full_name', read_only=True)

    class Meta:
        model  = Job
        fields = [
            'id', 'title', 'company_name', 'company_logo', 'employer_name',
            'category', 'job_type', 'experience_level', 'location', 'is_remote',
            'salary_range', 'status', 'deadline', 'views_count',
            'total_applications', 'created_at',
        ]


class JobDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer."""
    category           = CategorySerializer(read_only=True)
    category_id        = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True, required=False
    )
    salary_range       = serializers.ReadOnlyField()
    total_applications = serializers.ReadOnlyField()
    employer           = UserSerializer(read_only=True)

    class Meta:
        model  = Job
        fields = [
            'id', 'employer', 'category', 'category_id',
            'title', 'company_name', 'company_logo',
            'description', 'requirements', 'responsibilities', 'benefits',
            'job_type', 'experience_level', 'location', 'is_remote', 'skills_required',
            'salary_min', 'salary_max', 'salary_currency', 'salary_range',
            'status', 'deadline', 'views_count', 'total_applications',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employer', 'views_count', 'created_at', 'updated_at']


class ApplicationSerializer(serializers.ModelSerializer):
    applicant  = UserSerializer(read_only=True)
    job_title  = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company_name', read_only=True)

    class Meta:
        model  = Application
        fields = [
            'id', 'job', 'job_title', 'job_company',
            'applicant', 'cover_letter', 'resume',
            'status', 'applied_at', 'updated_at',
        ]
        read_only_fields = ['id', 'applicant', 'status', 'applied_at', 'updated_at']

    def validate_job(self, job):
        if job.status != Job.Status.ACTIVE:
            raise serializers.ValidationError('This job is not accepting applications.')
        user = self.context['request'].user
        if Application.objects.filter(job=job, applicant=user).exists():
            raise serializers.ValidationError('You have already applied for this job.')
        return job


class ApplicationStatusSerializer(serializers.ModelSerializer):
    """Employer-only: update application status."""
    class Meta:
        model  = Application
        fields = ['status', 'notes']


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)

    class Meta:
        model  = SavedJob
        fields = ['id', 'job', 'saved_at']
