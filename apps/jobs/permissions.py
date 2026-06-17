from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsEmployer(BasePermission):
    """Only employers can access."""
    message = 'Only employer accounts can perform this action.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_employer


class IsJobSeeker(BasePermission):
    """Only job seekers can access."""
    message = 'Only job seeker accounts can perform this action.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_job_seeker


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: owner can edit, others read-only."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, 'employer', None) or getattr(obj, 'applicant', None) or getattr(obj, 'user', None)
        return owner == request.user


class IsJobOwner(BasePermission):
    """Only the employer who posted the job."""

    def has_object_permission(self, request, view, obj):
        return obj.employer == request.user
