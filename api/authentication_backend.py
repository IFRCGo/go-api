from django.contrib.auth.backends import ModelBackend, UserModel
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.db.models import Q


class EmailBackend(ModelBackend):
    """
        To allow to authenticate with email too without needing
        to implement a custom User model at this point
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        '''
            Overriding: https://github.com/django/django/blob/master/django/contrib/auth/backends.py#L36
            most of it is working the same, only added a few more checks needed for the email auth
        '''

        # To make 'finally' work becase we have 'MultipleObjectsReturned' exception
        # which could still result in a valid login
        user = None
        shouldcheck = True

        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            shouldcheck = False
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        except MultipleObjectsReturned:
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('-is_active').first()

        if shouldcheck and \
                user and \
                user.check_password(password) and \
                self.user_can_authenticate(user):
            return user

    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

        return user if self.user_can_authenticate(user) else None
