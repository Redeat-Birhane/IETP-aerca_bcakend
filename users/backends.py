from django.contrib.auth.backends import BaseBackend # type: ignore
from users.models import CustomUser

class EmailBackend(BaseBackend):

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password):
            user.backend = 'users.backends.EmailBackend'
            return user
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
