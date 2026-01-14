from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
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
    CONTEXT_CHOICES = [
        ('normal', 'Звичайний стан'),
        ('post_meal', 'Після їжі'),
        ('post_meds', 'Після ліків'),
        ('post_exercise', 'Після активності'),
    ]

    _id = ObjectIdAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='glucose_stats')
    level = models.DecimalField(max_digits=5, decimal_places=2)
    measurement_date = models.DateTimeField()
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    context = models.CharField(
        max_length=20,
        choices=CONTEXT_CHOICES,
        default='normal',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-measurement_date']  # cортування: нові зверху


    def __str__(self):
        return f"{self.user.username} - {self.level} at {self.measurement_date}"

class BaseEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    note = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ['-timestamp']

class MealEvent(BaseEvent):
    carbs = models.DecimalField(max_digits=5, decimal_places=1, validators=[MinValueValidator(15)])

class MedicationEvent(BaseEvent):
    medicine_name = models.CharField(max_length=50)
    dosage = models.PositiveIntegerField()

class ActivityEvent(BaseEvent):
    activity_type = models.CharField(max_length=50)
    duration_minutes = models.PositiveIntegerField()