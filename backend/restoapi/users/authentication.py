# backend/users/authentication.py
# THIS IS A VERY SIMPLIFIED JWT AUTH EXAMPLE.
# IN PRODUCTION, USE A ROBUST LIBRARY LIKE djangorestframework-simplejwt.

import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from .models import User # Your custom User model

# It's better to get these from settings.py
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', 'your-super-secret-key-please-change')
JWT_ALGORITHM = getattr(settings, 'JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = getattr(settings, 'JWT_REFRESH_TOKEN_EXPIRE_DAYS', 7)


def generate_access_token(user: User) -> str:
    payload = {
        'user_id': str(user.id), # Ensure user.id is serializable (UUIDs are)
        'tenant_id': str(user.tenant_id) if user.tenant_id else None,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow(),
        'token_type': 'access'
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def generate_refresh_token(user: User) -> str:
    payload = {
        'user_id': str(user.id),
        'exp': datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow(),
        'token_type': 'refresh'
        # You might add a unique jti (JWT ID) here to allow blacklisting/revocation
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


class CustomJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()

        if not auth_header or auth_header[0].lower() != b'bearer':
            return None

        if len(auth_header) == 1:
            raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth_header) > 2:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        try:
            token = auth_header[1].decode('utf-8')
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Access token expired')
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed('Invalid access token')
        except UnicodeError:
            raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')


        if payload.get('token_type') != 'access':
            raise exceptions.AuthenticationFailed('Invalid token type. Access token required.')

        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed('User identifier not found in token')

        try:
            user = User.objects.select_related('tenant').get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        if not user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted.')

        return (user, token) # user will be request.user, token will be request.auth

    def authenticate_header(self, request):
        return 'Bearer'