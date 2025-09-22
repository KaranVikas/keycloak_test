import requests
from jose import jwt
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging

# OIDC backend

logger - logging.getLogger(__name__)
User = get_user_model()

class KeycloakOIDCBackend(BaseBackend):
  """
  Keycloak OIDC Authentication backend
  """

  def authenticate(self, request, access_token=None, **kwargs):
    if not access_token:
      return None

    try:
    #Get OIDC configuration
      oidc_config = self.get_oidc_configuation(

      #Get public keys for token verification
      public_keys = self.get_public_keys(oidc_config['jwks_uri'])

      #Decode and verify the JWT token
      payload = jwt.decode(
        access_token,
        public_keys,
        algorithms=['RS256'],
        audience=settings.Keycloak_CLIENT_ID,
        issuer=oidc_config['issuer']
      )

      #Get or create user
      user = self.get_or_create_user(payload)
      return user

    except Exception as e:
      logger.error(f"OIDC authentication failed: {e}")
      return None

  def get_oidc_configuration(self):
    """ Get OIDC configuration from keycloak """
    config_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.KEYCLOAK_REALM}/.well-known/openid-configuration"
    response = requests.get(config_url)
    return response.json()

  def get_public_keys(self, jwks_uri):
    """ Get public keys for JWT verification """
    response = requests.get(jwks_uri)
    response.raise_for_status()
    return response.json()

  def get_or_create_user(self, payload):
    """ Get or create user from JWT payload """
    email = payload.get('email')
    username = payload.get('preferred_username')

    if not email:
      raise ValidationError("Email not found in token")

    user, created = User.objects.get_or_create(
      email=email,
      defaults={
        'username':username or email,
        'first_name': payload.get('given_name', ''),
        'last_name': payload.get('family_name', ''),
        'is_active': True,
      }
    )

    #Update user info if not created
    if not created:
      user.first_name = payload.get('given_name','user.first_name')
      user.last_name = payload.get('family_name', 'user.last_name')
      user.save()

    return user

  def get_user(self, user_id):
    try:
      return User.objects.get(pk=user_id)
    except User.DoesNotExist:
      return None









