from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    hospital = models.CharField(max_length=50, null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    diabetes = models.CharField(max_length=20, null=True, blank=True)
    medic = models.CharField(max_length=30, null=True, blank=True)

# Create your models here.
