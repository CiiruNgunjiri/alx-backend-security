from django.utils.timezone import now
from .models import RequestLog, BlockedIP
from ipware import get_client_ip 
from django.http import HttpResponseForbidden
from django.conf import settings
from django.core.cache import cache
from django.contrib.gis.geoip2 import GeoIP2
from django.utils.deprecation import MiddlewareMixin

CACHE_TTL = 60 * 60 * 24  # 24 hours in seconds

class BlockingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip, _ = get_client_ip(request)
        if ip is None:
            ip = '0.0.0.0'

        # Check if IP is blocked
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access denied: Your IP is blocked.")

        response = self.get_response(request)
        return response
    
class IPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.geoip = GeoIP2(settings.GEOIP_PATH)
        
    def __call__(self, request):
         # Debug print to verify middleware is being called
        print(f"Logging IP for path: {request.path}")
        
        response = self.get_response(request)

        # Get client IP address
        ip, _ = get_client_ip(request)
        if ip is None:
            ip = '0.0.0.0'

        # Check cache for geolocation data
        geo_data = cache.get(f'geo_{ip}')
        if not geo_data:
            try:
                city_info = self.geoip.city(ip)
                country_info = self.geoip.country(ip)
                geo_data = {
                    'city': city_info.get('city', ''),
                    'country': country_info.get('country_name', ''),
                }
            except Exception:
                geo_data = {'city': '', 'country': ''}
            cache.set(f'geo_{ip}', geo_data, CACHE_TTL)

        country = geo_data.get('country', '')
        city = geo_data.get('city', '')
        # Create log entry with geolocation

        try:
        # Log the request details
            RequestLog.objects.create(
                ip_address=ip,
                timestamp=now(),
                path=request.path,
                country=country,
                city=city,
            )
        except Exception:
            # Silently ignore errors in logging
            pass
        
        return response

class GeoIPMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.geoip = GeoIP2()

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        if ip:
            request.geoip_location = self.geoip.city(ip)
        else:
            request.geoip_location = None
        response = self.get_response(request)
        return response
