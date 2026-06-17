import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    title           = django_filters.CharFilter(lookup_expr='icontains')
    company_name    = django_filters.CharFilter(lookup_expr='icontains')
    location        = django_filters.CharFilter(lookup_expr='icontains')
    job_type        = django_filters.ChoiceFilter(choices=Job.JobType.choices)
    experience_level = django_filters.ChoiceFilter(choices=Job.ExperienceLevel.choices)
    is_remote       = django_filters.BooleanFilter()
    category        = django_filters.NumberFilter(field_name='category__id')
    salary_min      = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max      = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    deadline_after  = django_filters.DateFilter(field_name='deadline', lookup_expr='gte')

    class Meta:
        model  = Job
        fields = [
            'title', 'company_name', 'location', 'job_type',
            'experience_level', 'is_remote', 'category',
            'salary_min', 'salary_max', 'deadline_after',
        ]
