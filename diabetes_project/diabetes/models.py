from django.conf import settings
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


class GlucoStats(models.Model):

    SOURCE_CHOICES = [
        ('manual', 'Ручне введення'),
        ('auto', 'Автоматично (CGM)'),
    ]

    _id = ObjectIdAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='glucose_stats')
    level = models.DecimalField(max_digits=5, decimal_places=2)
    measurement_date = models.DateTimeField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-measurement_date']  # cортування: нові зверху


    def __str__(self):
        return f"{self.user.username} - {self.level} at {self.measurement_date}"