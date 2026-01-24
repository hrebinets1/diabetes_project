from django.test import TestCase
from django.urls import reverse

from .models import CustomUser, GlucoStats
# Create your tests here.

class MedicTests(TestCase):
    def setUp(self):
        self.medic_password = "password_123"
        self.patient_password = "password123"

        self.medic = CustomUser.objects.create_user(
            username="medic_test", role="medic", hospital="Hospital", password=self.medic_password
        )
        self.patient = CustomUser.objects.create_user(
            username="patient_test", first_name="Oleksandr", last_name="Hrebinets", email="hreb@gmail.com",
            role="patient", diabetes="type1", medic="medic_test", password=self.patient_password
        )
        GlucoStats.objects.create(
            user=self.patient, level=10.0, context="post_meal", measurement_date="2026-01-20T10:00:00.000+00:00"
        )

    def test_authorization_correct_data(self):
        self.client.login(username=self.medic.username,password=self.medic_password)
        response = self.client.get(reverse('main_medic_page'))
        self.assertEqual(response.status_code, 200)

    def test_not_access_for_medic(self): #if you're a patient or non-authorized
        #login as patient
        self.client.login(username=self.patient.username,password=self.patient_password)
        response = self.client.get(reverse('main_medic_page'))
        self.assertRedirects(response, '/main_patient_page', fetch_redirect_response=False)
        self.client.logout()
        #non-authorized
        response = self.client.get(reverse('main_medic_page'))
        self.assertRedirects(response, '/auth_medic', fetch_redirect_response=False)

    def test_patient_info_on_medic_page(self):
        GlucoStats.objects.create(
            user=self.patient,
            level=5.5,
            context="fasting",
            measurement_date="2026-01-20T10:00:00.000+00:00",
        )
        self.client.login(username=self.medic.username,password=self.medic_password)
        response = self.client.get(reverse('main_medic_page'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Oleksandr")
        self.assertContains(response, "10") # created earlier in setUp function
        self.assertContains(response, "5.5")

    def test_medic_shows_patient_glucose_context(self):
        self.client.login(username=self.medic.username, password=self.medic_password)
        #old info
        GlucoStats.objects.create(
            user=self.patient,
            level=5.0,
            context="normal",  # Натщесерце
            measurement_date="2026-01-24T10:00:00.000+00:00"
        )

        response = self.client.get(reverse('main_medic_page'))
        patient_data = response.context['patients'][0]

        self.assertEqual(float(patient_data['last_glucose']), 5.0)
        self.assertEqual(patient_data['context_display'], 'Натщесерце')

        #new info
        GlucoStats.objects.create(
            user=self.patient,
            level=9.0,
            context="post_meal",  # Після їжі
            measurement_date="2026-01-24T12:00:00.000+00:00"
        )

        response = self.client.get(reverse('main_medic_page'))
        patient_data = response.context['patients'][0]

        self.assertEqual(float(patient_data['last_glucose']), 9.0)
        self.assertEqual(patient_data['context_display'], 'Після їжі')

    def test_no_patient_info_on_medic_page(self):
        med_pass = "password_123"
        med = CustomUser.objects.create_user(
            username="new_medic",
            role="medic",
            hospital="Hospital",
            password=med_pass
        )
        self.client.login(username=med.username, password=med_pass)

        response = self.client.get(reverse('main_medic_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "На даний момент за Вами не закріплено пацієнтів для аналізу.")
