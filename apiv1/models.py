import hashlib, time, uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    """
    Model manager for User without 'username', 'first_name', and 'last_name'.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    def get_current_time_hash():
        return hashlib.sha1(str(time.time()).encode('utf-8')).hexdigest()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    first_name = None
    last_name = None
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=40, default=get_current_time_hash, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ['-date_joined']


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_version = models.SmallIntegerField()
    os = models.CharField(max_length=10)
    fcm_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='devices', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-modified_at']


class Highlight(models.Model):
    # uniqueness is enforced in model serializer
    uid = models.UUIDField(unique=False)
    # key e.g. TB;Mat;1;1
    # uniqueness is enforced in model serializer
    key = models.CharField(max_length=30, unique=False)
    verse = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField()
    modified_at = models.DateTimeField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='highlights', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-modified_at']


class Note(models.Model):
    # uniqueness is enforced in model serializer
    uid = models.UUIDField(unique=False)
    # TODO format?
    key = models.CharField(max_length=150, blank=True, null=True)
    title = models.CharField(max_length=150, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    modified_at = models.DateTimeField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notes', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-modified_at']
