from django.contrib import admin
from .models import Category, Job, Application, SavedJob


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display   = ['title', 'company_name', 'employer', 'job_type', 'status', 'deadline', 'created_at']
    list_filter    = ['status', 'job_type', 'experience_level', 'is_remote']
    search_fields  = ['title', 'company_name', 'location']
    raw_id_fields  = ['employer']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering       = ['-created_at']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display  = ['applicant', 'job', 'status', 'applied_at']
    list_filter   = ['status']
    search_fields = ['applicant__email', 'job__title']
    raw_id_fields = ['applicant', 'job']
    readonly_fields = ['applied_at']


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'saved_at']
    raw_id_fields = ['user', 'job']
