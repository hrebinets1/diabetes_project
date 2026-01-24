from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .analysis import analyze_glucose_data, calculate_current_status
from .forms import RegisterPatientForm
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

class PatientTests(TestCase):
    def setUp(self):
        self.medic_password = "123456"
        self.patient_password = "123_456"

        self.medic = CustomUser.objects.create_user(
            username="testmed", first_name="Alex", last_name="Kat", email="med@g.com",
            role="medic", hospital="№1", position="doctor", password=self.medic_password
        )
        self.patient = CustomUser.objects.create_user(
            username="testpat", first_name="Mksm", last_name="Blc", email="pat@g.com",
            role="patient", hospital="№1", diabetes="type1", medic="medic_test", password=self.patient_password
        )


    def test_auth_correct_data(self):
        self.client.login(username=self.patient.username,password=self.patient_password)
        response = self.client.get(reverse('main_patient_page'))
        self.assertEqual(response.status_code, 200)

    def test_main_page_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('main_patient_page'))
        # Має перекинути на логін
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth_patient', response.url)
        self.assertRedirects(response, '/auth_patient', fetch_redirect_response=False)

    def test_main_page_load_success(self):
        self.client.login(username='testpat', password='123_456')
        response = self.client.get(reverse('main_patient_page'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_patient_page.html')
        # наявність контексту
        self.assertIn('current_level', response.context)
        self.assertIn('gluco_form', response.context)

    def test_gluco_stats_creation(self):
        stat = GlucoStats.objects.create(
            user=self.patient,
            level=5.5,
            measurement_date=timezone.now(),
            source='manual',
            context='normal'
        )
        self.assertIsNotNone(stat.pk)
        self.assertEqual(stat.level, 5.5)

    def test_analyze_glucose_data(self):
        now = timezone.now()
        GlucoStats.objects.create(user=self.patient, level=4.0, measurement_date=now - timedelta(hours=2))
        GlucoStats.objects.create(user=self.patient, level=6.0, measurement_date=now - timedelta(hours=1))

        queryset = GlucoStats.objects.filter(user=self.patient)
        result = analyze_glucose_data(self.patient, queryset, period_days=7)

        # Перевіряємо математику
        stats = result['stats']
        self.assertEqual(stats['avg'], 5.0)
        self.assertEqual(stats['min'], 4.0)
        self.assertEqual(stats['max'], 6.0)

        expected_hba1c = round((5.0 + 2.59) / 1.59, 1)
        self.assertEqual(stats['hba1c'], expected_hba1c)

    def test_analyze_empty_data(self):
        queryset = GlucoStats.objects.none()
        result = analyze_glucose_data(self.patient, queryset)
        self.assertEqual(result['stats']['avg'], 0)
        self.assertEqual(len(result['history']), 0)

    def test_register_form_valid(self):
        form_data = {
            'username': 'newpat',
            'email': 'np@g.com',
            'password': '567890',
            'password_confirm': '567890',
            'first_name': 'Val',
            'last_name': 'Er',
            'diabetes': 'type1',
            'medic': 'testmed',  # існуючий лікар
            'hospital': '№1'
        }
        form = RegisterPatientForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_register_form_invalid_medic(self):
        form_data = {
            'username': 'newpat2',
            'password': '345678',
            'password_confirm': '345678',
            'medic': 'nonndoc'  # такого немає
        }
        form = RegisterPatientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Лікар з таким username не знайдений!", form.errors['medic'])

    def test_calculate_current_status_hypo(self):
        res = calculate_current_status(2.5, 'normal', 'type1')
        self.assertEqual(res['status'], 'Гіпоглікемія')
        self.assertEqual(res['color'], 'Red')

    def test_post_gluco_stats(self):
        self.client.login(username='testpat', password='123_456')

        data = {
            'submit_gluco': '',  # імітація натискання кнопки
            'gluco-level': '7.3',
            'gluco-measurement_date': '2026-01-24T12:00',
            'gluco-context': 'post_meal'
        }
        response = self.client.post(reverse('main_patient_page'), data)
        self.assertEqual(response.status_code, 302)
        # чи записалось в БД
        self.assertTrue(GlucoStats.objects.filter(user=self.patient, level=7.3).exists())


