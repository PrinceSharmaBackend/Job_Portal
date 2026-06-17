from django.urls import path
from .views import (
    CategoryListView,
    JobListView,
    JobDetailView,
    EmployerJobListCreateView,
    EmployerJobDetailView,
    ApplyJobView,
    MyApplicationsView,
    DeleteApplicationView,
    JobApplicationsView,
    UpdateApplicationStatusView,
    SavedJobListView,
    SaveUnsaveJobView,
    EmployerDashboardView,
    JobSeekerDashboardView,
)

urlpatterns = [
    # ── Public ──────────────────────────────────────────────────────────────────
    path('categories/',              CategoryListView.as_view(),          name='categories'),
    path('',                         JobListView.as_view(),               name='job-list'),
    path('<int:pk>/',                JobDetailView.as_view(),             name='job-detail'),

    # ── Employer ─────────────────────────────────────────────────────────────
    path('employer/jobs/',           EmployerJobListCreateView.as_view(), name='employer-jobs'),
    path('employer/jobs/<int:pk>/',  EmployerJobDetailView.as_view(),     name='employer-job-detail'),
    path('employer/jobs/<int:job_id>/applications/', JobApplicationsView.as_view(), name='job-applications'),
    path('employer/applications/<int:pk>/status/',  UpdateApplicationStatusView.as_view(), name='update-application-status'),
    path('employer/dashboard/',      EmployerDashboardView.as_view(),     name='employer-dashboard'),

    # ── Job Seeker ───────────────────────────────────────────────────────────
    path('apply/',                   ApplyJobView.as_view(),              name='apply-job'),
    path('my-applications/',         MyApplicationsView.as_view(),        name='my-applications'),
    path('my-applications/<int:pk>/withdraw/', DeleteApplicationView.as_view(), name='withdraw-application'),
    path('saved/',                   SavedJobListView.as_view(),          name='saved-jobs'),
    path('<int:job_id>/save/',       SaveUnsaveJobView.as_view(),         name='save-job'),
    path('dashboard/',               JobSeekerDashboardView.as_view(),    name='seeker-dashboard'),
]
