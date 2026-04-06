from django.contrib import admin
from .models import Location, DistributionRequest

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']

@admin.register(DistributionRequest)
class DistributionRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'user', 'status', 'created_at', 'phone']
    list_filter = ['status', 'business_type']
    search_fields = ['company_name', 'contact_person', 'phone', 'email']
    list_editable = ['status']