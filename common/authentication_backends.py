from django.contrib.auth.models import User

class EmailAuthBackend(object):
    def authenticate(self, username=None, password=None):
        # Check the token and return a User.
        if not username or not password:
            return None
        if '@' in username:
            kwargs = {'email': username}
        else:
             kwargs = {'username': username}
        try:
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
        except:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
