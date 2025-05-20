from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

"""
Harusnya ini udh ga dipake, diganti total jadi pake yg punya allauth
(kalo mau cek, cek di tabletennis/settings.py di AUTHENTICATION_BACKENDS
msh ada path ke file ini ato engga)
'accounts.backends.EmailBackend' <-- yg ini
"""

class EmailBackend(ModelBackend):
    """
    Authenticate using email and password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # username parameter here will actually hold the email
        if username is None:
            username = kwargs.get('email')
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
