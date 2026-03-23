from django.contrib import admin
from .models import Plan, Subscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_active', 'status', 'end_date']
    list_filter = ['is_active', 'status']
    search_fields = ['user__username', 'plan__name']
    list_editable = ['is_active']
    date_hierarchy = 'end_date'