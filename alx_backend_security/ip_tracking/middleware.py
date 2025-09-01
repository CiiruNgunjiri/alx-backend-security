from django.utils.timezone import now
from .models import RequestLog, BlockedIP
from ipware import get_client_ip 
from django.http import HttpResponseForbidden


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

class IPLoggingAndBlockingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip, is_routable = get_client_ip(request)
        if ip is None:
            ip = '0.0.0.0'

        # Check if IP is blocked
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access denied: Your IP is blocked.")

        # Log the IP request as before
        from django.utils.timezone import now
        from .models import RequestLog
        
        RequestLog.objects.create(ip_address=ip, timestamp=now(), path=request.path)

        response = self.get_response(request)
        return response
    
