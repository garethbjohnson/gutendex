import os
from django.http import JsonResponse

def require_app_secret(view_func):
    def wrapped_view(request, *args, **kwargs):
        client_secret = request.headers.get('X-App-Secret')
        server_secret = os.environ.get('APP_SHARED_SECRET')
        
        # Check if the secret matches your frontend application's token
        if not server_secret or client_secret != server_secret:
            return JsonResponse({'error': 'Unauthorized access'}, status=403)
            
        return view_func(request, *args, **kwargs)
    return wrapped_view