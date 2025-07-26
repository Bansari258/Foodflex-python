# foodflex/middleware.py
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)

class JWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()

    def __call__(self, request):
        public_paths = [
            reverse('users:landing'),
            reverse('users:signup'),
            reverse('users:api_signup'),
            reverse('users:api_login'),
            reverse('users:help'),
            reverse('vendor:vendor_landing'),
            reverse('vendor:vendor_signup'),
            reverse('vendor:api_vendor_signup'),
            reverse('vendor:api_vendor_login'),
            reverse('vendor:profile_setup'),
            reverse('vendor:api_profile_setup'),
        ]
        admin_paths = [
            '/admin/',
            '/admin/login/',
            '/admin/logout/',
        ]
        token_refresh_path = reverse('users:token_refresh')
        if (request.path in public_paths or
                any(request.path.startswith(admin_path) for admin_path in admin_paths) or
                request.path == token_refresh_path):
            logger.debug(f"Public, admin, or token refresh path accessed, skipping JWT authentication: {request.path}")
            return self.get_response(request)

        if request.user.is_authenticated:
            logger.debug(f"User authenticated via session for path {request.path}: {request.user.email}")
            return self.get_response(request)
        auth_header = request.headers.get('Authorization', None)
        token = None
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                logger.debug(f"Found token in Authorization header: {token}")
            else:
                logger.warning(f"Invalid Authorization header format for path: {request.path}, header: {auth_header}")
        else:
            token = request.COOKIES.get('access_token')
            if token:
                logger.debug(f"Found token in cookies: {token}")
            else:
                logger.warning(f"Missing Authorization header and cookie for path: {request.path}")
                return HttpResponseRedirect(reverse('users:landing'))

        try:
            validated_token = self.jwt_authenticator.get_validated_token(token)
            user = self.jwt_authenticator.get_user(validated_token)
            request.user = user
            logger.debug(f"User authenticated via JWT for path {request.path}: {user.email}")
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid token for path: {request.path}, error: {str(e)}")
            return HttpResponseRedirect(reverse('users:landing'))
        except Exception as e:
            logger.error(f"Error during JWT authentication for path {request.path}: {str(e)}", exc_info=True)
            return HttpResponseRedirect(reverse('users:landing'))

        return self.get_response(request)