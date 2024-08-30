import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from requests_oauthlib import OAuth2Session
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth import get_user_model

# OAuth2 Client Setup
oauth = OAuth2Session(client_id=settings.GOOGLE_CLIENT_ID, redirect_uri=settings.GOOGLE_REDIRECT_URI)


def google_login(request):
    oauth = OAuth2Session(
        settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        scope=['profile', 'email']
    )
    authorization_url, state = oauth.authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        access_type='offline'
    )
    request.session['oauth_state'] = state
    return redirect(authorization_url)


@csrf_exempt
def google_callback(request):
    state = request.session.get('oauth_state')
    oauth = OAuth2Session(
        settings.GOOGLE_CLIENT_ID,
        state=state,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    code = request.GET.get('code')
    if not code:
        return JsonResponse({'error': 'Authorization code is missing.'}, status=400)

    # Fetch the token
    token = oauth.fetch_token(
        'https://oauth2.googleapis.com/token',
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        code=code
    )
    print("token")
    print(token)
    # Get user info
    response = oauth.get('https://www.googleapis.com/oauth2/v2/userinfo')
    user_info = response.json()

    # Get or create the user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        email=user_info['email'],
        defaults={
            'first_name': user_info.get('given_name'),
            'last_name': user_info.get('family_name'),
            'username': user_info.get('email')  # Make username the email
        }
    )

    # Log the user in
    auth_login(request, user)

    # Optionally return user info as JSON
    return JsonResponse({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email
    })



@login_required
@csrf_exempt
def get_user_details(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)

    user = request.user
    return JsonResponse({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    })

@csrf_exempt
def logout(request):
    auth_logout(request)
    request.session.flush()  # Ensure session is cleared
    return JsonResponse({'message': 'Successfully logged out.'})

def say_hi(request):
    return JsonResponse({"hello":"hi"})


