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
        # To make 'finally' work becase we have 'MultipleObjectsReturned' exception
        # which could still result in a valid login
        user = None
        shouldcheck = True

        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            shouldcheck = False
            UserModel().set_password(password)
        except MultipleObjectsReturned:
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).order_by('id').first()

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
