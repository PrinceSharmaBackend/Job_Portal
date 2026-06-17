from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .emails import (
    send_application_received_email,
    send_new_application_email_to_employer,
    send_application_status_email,
)

from .models import Category, Job, Application, SavedJob
from .serializers import (
    CategorySerializer,
    JobListSerializer,
    JobDetailSerializer,
    ApplicationSerializer,
    ApplicationStatusSerializer,
    SavedJobSerializer,
)
from .permissions import IsEmployer, IsJobSeeker, IsJobOwner
from .filters import JobFilter


# ─── Category Views ───────────────────────────────────────────────────────────

class CategoryListView(generics.ListAPIView):
    """Public: list all job categories."""
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    permission_classes = [permissions.AllowAny]


# ─── Job Views ────────────────────────────────────────────────────────────────

class JobListView(generics.ListAPIView):
    """
    Public: List all ACTIVE jobs with search, filter, and ordering.

    Search fields  : title, company_name, location, skills_required
    Filter fields  : job_type, experience_level, is_remote, category, salary range
    Ordering fields: created_at, salary_min, views_count
    """
    serializer_class   = JobListSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class    = JobFilter
    search_fields      = ['title', 'company_name', 'location', 'skills_required', 'description']
    ordering_fields    = ['created_at', 'salary_min', 'views_count']
    ordering           = ['-created_at']

    def get_queryset(self):
        return Job.objects.filter(status=Job.Status.ACTIVE).select_related('employer', 'category')


class JobDetailView(generics.RetrieveAPIView):
    """Public: Full job details — increments view count."""
    serializer_class   = JobDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset           = Job.objects.filter(status=Job.Status.ACTIVE)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Job.objects.filter(pk=instance.pk).update(views_count=instance.views_count + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class EmployerJobListCreateView(generics.ListCreateAPIView):
    """Employer: list own jobs + create new job."""
    permission_classes = [IsEmployer]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobDetailSerializer
        return JobListSerializer

    def get_queryset(self):
        return Job.objects.filter(employer=self.request.user).select_related('category')

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)


class EmployerJobDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Employer: retrieve / update / delete own job."""
    permission_classes = [IsEmployer, IsJobOwner]
    serializer_class   = JobDetailSerializer
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Job.objects.filter(employer=self.request.user)


# ─── Application Views ────────────────────────────────────────────────────────

class ApplyJobView(generics.CreateAPIView):
    """Job Seeker: apply for a job."""
    serializer_class   = ApplicationSerializer
    permission_classes = [IsJobSeeker]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)
        send_application_received_email(application)
        send_new_application_email_to_employer(application)


class MyApplicationsView(generics.ListAPIView):
    """Job Seeker: view all my applications."""
    serializer_class   = ApplicationSerializer
    permission_classes = [IsJobSeeker]

    def get_queryset(self):
        return Application.objects.filter(
            applicant=self.request.user
        ).select_related('job', 'job__employer')


class DeleteApplicationView(generics.DestroyAPIView):
    """Job Seeker: withdraw (delete) a previously submitted application."""
    permission_classes = [IsJobSeeker]

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status not in [Application.Status.PENDING]:
            return Response(
                {'error': 'You can only withdraw pending applications.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response({'message': 'Application withdrawn successfully.'}, status=status.HTTP_200_OK)


class JobApplicationsView(generics.ListAPIView):
    """Employer: view all applications for a specific job."""
    serializer_class   = ApplicationSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        job = get_object_or_404(Job, pk=self.kwargs['job_id'], employer=self.request.user)
        return Application.objects.filter(job=job).select_related('applicant')


class UpdateApplicationStatusView(generics.UpdateAPIView):
    """Employer: update application status (shortlist, reject, hire, etc.)."""
    serializer_class   = ApplicationStatusSerializer
    permission_classes = [IsEmployer]

    def get_queryset(self):
        return Application.objects.filter(job__employer=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_application_status_email(instance)
        return Response({'message': 'Application status updated.', 'data': serializer.data})


# ─── Saved Jobs ───────────────────────────────────────────────────────────────

class SavedJobListView(generics.ListAPIView):
    """Job Seeker: list saved/bookmarked jobs."""
    serializer_class   = SavedJobSerializer
    permission_classes = [IsJobSeeker]

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related('job')


class SaveUnsaveJobView(APIView):
    """Job Seeker: toggle save/unsave a job."""
    permission_classes = [IsJobSeeker]

    def post(self, request, job_id):
        job = get_object_or_404(Job, pk=job_id, status=Job.Status.ACTIVE)
        saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if not created:
            saved.delete()
            return Response({'message': 'Job removed from saved list.', 'saved': False})
        return Response({'message': 'Job saved successfully.', 'saved': True}, status=status.HTTP_201_CREATED)


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

class EmployerDashboardView(APIView):
    """Employer: quick stats dashboard."""
    permission_classes = [IsEmployer]

    def get(self, request):
        jobs = Job.objects.filter(employer=request.user)
        data = {
            'total_jobs':        jobs.count(),
            'active_jobs':       jobs.filter(status=Job.Status.ACTIVE).count(),
            'total_applications': Application.objects.filter(job__employer=request.user).count(),
            'pending_applications': Application.objects.filter(
                job__employer=request.user, status=Application.Status.PENDING
            ).count(),
            'shortlisted': Application.objects.filter(
                job__employer=request.user, status=Application.Status.SHORTLISTED
            ).count(),
        }
        return Response(data)


class JobSeekerDashboardView(APIView):
    """Job Seeker: quick stats dashboard."""
    permission_classes = [IsJobSeeker]

    def get(self, request):
        applications = Application.objects.filter(applicant=request.user)
        data = {
            'total_applications': applications.count(),
            'pending':     applications.filter(status=Application.Status.PENDING).count(),
            'reviewing':   applications.filter(status=Application.Status.REVIEWING).count(),
            'shortlisted': applications.filter(status=Application.Status.SHORTLISTED).count(),
            'rejected':    applications.filter(status=Application.Status.REJECTED).count(),
            'hired':       applications.filter(status=Application.Status.HIRED).count(),
            'saved_jobs':  SavedJob.objects.filter(user=request.user).count(),
        }
        return Response(data)
