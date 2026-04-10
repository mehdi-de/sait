import uuid
from datetime import date, timedelta
from django.utils import timezone
from .models import Visitor 

class UniqueVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        visitor_id = request.COOKIES.get('visitor_id')
        today = timezone.now().date()

        
        if not visitor_id:
            visitor_id = str(uuid.uuid4())
            
            response = self.get_response(request)
           
            response.set_cookie('visitor_id', visitor_id, max_age=60*60*24*365, httponly=True, samesite='Lax')
        else:
            
            response = self.get_response(request)

        
        try:
          
            last_visit = Visitor.objects.filter(visitor_id=visitor_id, visit_time__date=today).first()

            
            if not last_visit:
                Visitor.objects.create(visitor_id=visitor_id, visit_time=timezone.now())
        except Exception as e:
            
            print(f"Error saving visitor: {e}")

       
        request.visitor_id = visitor_id
        return response