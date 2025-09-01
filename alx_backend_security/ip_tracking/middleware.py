from django.utils.timezone import now
from .models import RequestLog
from ipware import get_client_ip  # django-ipware

class IPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
         # Debug print to verify middleware is being called
        print(f"Logging IP for path: {request.path}")
        
        response = self.get_response(request)

        # Get client IP address
        ip, is_routable = get_client_ip(request)
        if ip is None:
            ip = '0.0.0.0'

        # Log the request details
        RequestLog.objects.create(
            ip_address=ip,
            timestamp=now(),
            path=request.path
        )

        return response
