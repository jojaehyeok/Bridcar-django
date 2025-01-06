import jwt

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions

class UserAuthenticationMiddleware(TokenAuthentication):
    def authenticate(self, request):
        User = get_user_model()
        authorization_heaader = request.headers.get('Authorization')

        if authorization_heaader:
            try:
                access_token = authorization_heaader.split(' ')[1]

                payload = jwt.decode(
                    access_token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )

            except jwt.ExpiredSignatureError:
                raise exceptions.NotAuthenticated('EXPIRED_TOKEN')
            except IndexError:
                raise exceptions.NotAuthenticated('INVALID_TOKEN')

            user = User.objects \
                .filter(pk=payload['user_id']) \
                .first()

            if user is None:
                raise exceptions.AuthenticationFailed('USER_NOT_FOUND')
            elif not user.is_active:
                raise exceptions.AuthenticationFailed('INACTIVE_USER')

            now = timezone.now()

            return (user, None)
        else:
            user = getattr(request._request, 'user', None)

            if not user or not user.is_active:
                return None

            return (user, None)
