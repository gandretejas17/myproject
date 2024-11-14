from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, Group, User

class EmailOrUsernameModelBackend(object):

    def authenticate(self, username=None, password=None):
        kwargs = {'email': username} if '@' in username else {'username': username}
        try:
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


""" Import all the models """
# from .model.users import User
from .model.base import Base
from .model.roles import Roles
from .model.student import Student


