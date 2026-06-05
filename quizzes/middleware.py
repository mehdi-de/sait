import socket
from django.utils import timezone
from django.http import HttpResponse
from .models import VisitorStats, IPVisit

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)
        
        if request.path in ['/', '/home/']:
            today = timezone.now().date()
            
            # فقط unique IP track کن
            ip_visit, created = IPVisit.objects.get_or_create(
                ip_address=ip,
                date=today
            )
            
            # فقط unique visitors آپدیت کن (visits_today حذف شد)
            stats, _ = VisitorStats.objects.get_or_create(date=today)
            stats.unique_visitors_today = IPVisit.objects.filter(date=today).count()
            stats.save()
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip.strip()