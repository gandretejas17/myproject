from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils.translation import gettext_lazy as _
import re
from ..model.roles import Roles


class CustomUserManager(UserManager):
    def _create_user(self, username, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('mobile', username)
        # group, created = Group.objects.get_or_create(name='super_admin')
        # extra_fields.setdefault('group_id', group.id)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)


class UserPermissionMixin(PermissionsMixin):
    is_superuser = models.BooleanField(_('superuser status'),
                                       default=False,
                                       help_text=_(
                                           'Designates that this user has all permissions without '
                                           'explicitly assigning them.'
                                       ),
                                       )

    groups = None
    user_permissions = None
    is_staff = False

    class Meta:
        abstract = True

    def get_group_permissions(self, obj=None):
        pass

    def get_all_permissions(self, obj=None):
        pass


class User(AbstractBaseUser,PermissionsMixin):
    """
        An abstract base class implementing a fully featured User model with
        admin-compliant permissions.

        email and password are required. Other fields are optional.
        is_superuser/ is_staff : for superuser, admin this is true
        is_verified : users in category dealership and showrooms are verified by admin
        """
    
    objects = CustomUserManager()
    email_hash = models.CharField(blank=True, null=True, max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    otp_time = models.DateTimeField(blank=True, null=True)
    hash_time = models.DateTimeField(blank=True, null=True,)
    
    first_name = models.CharField(_('first name'), max_length=255, blank=True, null=True)
    last_name = models.CharField(_('last name'), max_length=255, blank=True, null=True)
    email = models.EmailField(_('email address'), null=True, blank=True)
    mobile = models.CharField(_('mobiles'), max_length=16, null=True, blank=True, db_index=True)
    username = models.CharField(
        _('username'),
        max_length=150,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        null=True,
        blank=True, unique=True, db_index=True
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )    
    STATUS_CHOICES = ((1, 'Active'),(2, 'Inactive'),(3,'Deleted'),)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=1, db_index=True)

    # Relationships
    created_by = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True, related_name='role_user')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = _('users')
        verbose_name_plural = _('users')

        indexes = (
            models.Index(fields=("email", "status", "mobile",),),
            models.Index(fields=("email", "status"),),
            models.Index(fields=("mobile", "status"),),
            models.Index(fields=("first_name", "last_name","status",),),
        )
    def __str__(self):
        return str(self.pk)
    
    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        if self.first_name and self.last_name:
            full_name = f"{self.first_name} {self.last_name}"
            return full_name.strip()

    @property
    def check_email(self):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return True if re.match(pattern, self.email) else False
    
    @staticmethod
    def to_dict(instance):
        resp_dict = {}
        resp_dict["id"] = instance.id
        resp_dict["first_name"] = instance.first_name
        resp_dict["last_name"] = instance.last_name
        resp_dict["full_name"] = instance.get_full_name() if instance.first_name and instance.last_name else "-"
        
        resp_dict["email"] = instance.email if instance.email else "-"
        resp_dict["mobile"] = instance.mobile if instance.mobile else "-"
        
        if username := instance.username:    
            resp_dict["username"] = username
        
        resp_dict["status"] = instance.status
        resp_dict["status_name"] = instance.get_status_display()
        
        if instance.role_id:
            resp_dict["role"] = instance.role.id
            resp_dict["role_name"] = instance.role.name
            resp_dict['role_status'] = instance.role.status
            resp_dict['role_status_name'] = instance.role.get_status_display()
        
        resp_dict["is_pass_set"] = True if instance.password else False

        resp_dict["created_at"] = instance.created_at
        resp_dict["updated_at"] = instance.updated_at

        return resp_dict