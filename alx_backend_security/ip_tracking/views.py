from django_ratelimit.decorators import ratelimit
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.shortcuts import redirect

def get_rate(request):
    if request.user.is_authenticated:
        return '10/m'
    return '5/m'

@ratelimit(key='user_or_ip', rate=get_rate, block=True)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Return JSON success response or redirect URL in JSON
            return JsonResponse({'message': 'Login successful'})
        else:
            # Invalid login JSON response with 401 Unauthorized status
            return JsonResponse({'error': 'Invalid username or password'}, status=401)
    
    # Reject GET requests or others since no HTML form will be served
    return JsonResponse({'error': 'POST request required'}, status=405)
