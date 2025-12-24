from django.contrib.auth.models import AbstractUser
from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField

class CustomUser(AbstractUser):
    _id = ObjectIdAutoField(primary_key=True)
    hospital = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=20, blank=True)
    medic = models.CharField(max_length=20, blank=True)
    diabetes = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, null=False,
                            choices = [('medic', 'Medic'), ('patient', 'Patient')], default='medic')