from django.http import JsonResponse
import requests
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from urllib.parse import urlencode
import uuid
import json
from .oidc import KeycloakOIDCBackend


def keycloak_login(request):
  """ Initiate OIDC login """
  state = str(uuid.uuid4())
  request.session['oidc_state'] = state

  params = {
    'client_id': settings.KEYCLOAK_CLIENT_ID,
    'redirect_uri': settings.KEYCLOAK_REDIRECT_URI,
    'response_type': 'code',
    'scope': 'openid profile email',
    'state': state,

  }

  auth_url = f"{setttings.KEYCLOAK_CLIENT_ID}/realms/{settings.KEYCLOAK_CLIENT_ID}/protocol/openid-connect/auth"
  return redirect(f"{auth_url}?{urlencode(params)}")

def keycloak_callback(request):
  """ Handle OIDC callback  """
  code = request.GET.get('code')
  state = request.GET.get('state')

  #verify data
  if not state or state != request.session.get('oidc_State'):
    return JsonResponse({'error': 'Invalid state'}, status=400)

  if not code:
    return JsonResponse({'error' : 'Authorization code not required'}, status=400)

  try:
    #Exchange code for tokens
    tokens = exchange_code_for_tokens(code)

    #Authenticate user
    backend = KeycloakOIDCBackend()
    user = backend.authenticate(request, access_token=tokens['access_token'])

    if user:
      login(request, user, backend='todo.auth.oidc.KeycloakOIDCBackend')
      return redirect('/')
    else:
      return JsonResponse({'error': 'Authentication failed'}, status=400)

  except Exception as e:
    return JsonResponse({'error': str(e)}, status=500)

def exhange_code_for_tokens(code):
  """ Exchange authorization code for tokens """
  tokens = exchange_code_for_tokens(code)

  #authentication user
  backend = KeycloakOIDCBackend()
  user = backend.authenticate(request, access_token=tokens['access_token'])

  if user:
    login(request, user, backend='todo.auth.oidc.keycloakOIDCBackend')
    return redirect('/')
  else:
    return JsonResponse({'error': 'Authentication failed'}, status=400)

except Exception as e:
  return JsonResponse({'error': str(e)}, status=500)

@login_required
def keycloak_logout(request):
  """ Logout user from django and Keycloak """
  logout_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"

  params = {
    'client_id': settings.KEYCLOAK_CLIENT_ID,
    'post_logout_redirect_uri': request.build_absolute_uri('/'),
  }

  logout(request)
  return redirect(f"{logout_url}?{urlencode(params)}")



