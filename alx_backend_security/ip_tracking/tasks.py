from celery import shared_task
from django.utils.timezone import now, timedelta
from ip_tracking.models import SuspiciousIP, RequestLog
from django.db.models import Count, Q

@shared_task
def flag_suspicious_ips():
    one_hour_ago = now() - timedelta(hours=1)

    # Query for IPs with more than 100 requests in the last hour
    high_volume_ips = (RequestLog.objects
                       .filter(timestamp__gte=one_hour_ago)
                       .values('ip_address')
                       .annotate(request_count=Count('id'))
                       .filter(request_count__gt=5)
                       .values_list('ip_address', flat=True))

    # Query for IPs accessing sensitive paths '/admin' or '/login' in the last hour
    sensitive_paths = ['/admin', '/login']
    sensitive_access_ips = (RequestLog.objects
                            .filter(timestamp__gte=one_hour_ago)
                            .filter(Q(path__startswith='/admin') | Q(path__startswith='/login'))
                            .values_list('ip_address', flat=True)
                            .distinct())
    
    flagged_ips = set(list(high_volume_ips) + list(sensitive_access_ips))

    for ip in flagged_ips:
        reasons = []
        if ip in high_volume_ips:
            reasons.append('Exceeded 5 requests per hour')
        if ip in sensitive_access_ips:
            reasons.append('Accessed sensitive path')

        SuspiciousIP.objects.update_or_create(
            ip_address=ip,
            defaults={'reason': '; '.join(reasons)}
        )
