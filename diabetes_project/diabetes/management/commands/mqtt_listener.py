import json
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.conf import settings
import paho.mqtt.client as mqtt
from django.contrib.auth import get_user_model

from ...models import CustomUser, GlucoStats, MealEvent, MedicationEvent, ActivityEvent

User = get_user_model()

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        client.connect("localhost", 1883, 60)

        try:
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Stopping MQTT client'))

    def on_connect(self, client, userdata, flags, rc):
        self.stdout.write(self.style.SUCCESS('Connected via MQTT! Listening.'))
        client.subscribe("devices/glucose")

    # визначення контексту вимірювання
    def determine_context(self, user, measurement_time):

        # останні події за 2 години
        time_threshold = measurement_time - timedelta(hours=2)

        last_meal = MealEvent.objects.filter(
            user=user, timestamp__gte=time_threshold, timestamp__lte=measurement_time
        ).order_by('-timestamp').first()

        last_meds = MedicationEvent.objects.filter(
            user=user, timestamp__gte=time_threshold, timestamp__lte=measurement_time
        ).order_by('-timestamp').first()

        last_activity = ActivityEvent.objects.filter(
            user=user, timestamp__gte=time_threshold, timestamp__lte=measurement_time
        ).order_by('-timestamp').first()

        events = []
        if last_meal:
            events.append((last_meal.timestamp, 'post_meal'))
        if last_meds:
            events.append((last_meds.timestamp, 'post_meds'))
        if last_activity:
            events.append((last_activity.timestamp, 'post_exercise'))

        if not events:
            return 'normal'

        latest_event = max(events, key=lambda x: x[0])

        return latest_event[1]

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)

            device_sn = data.get('device_id')
            timestamp_str = data.get('timestamp')

            # Парсинг часу у datetime object (timezone aware)
            measurement_bt = parse_datetime(timestamp_str)

            if not measurement_bt:
                measurement_bt = timezone.now()
            elif timezone.is_naive(measurement_bt):
                measurement_bt = timezone.make_aware(measurement_bt)

            user = User.objects.get(device_id=device_sn)

            calculated_context = self.determine_context(user, measurement_bt)

            GlucoStats.objects.create(
                user=user,
                level=data['level'],
                measurement_date=measurement_bt,
                source='auto',
                context=calculated_context
            )

            self.stdout.write(
                self.style.SUCCESS(f"{data['level']} mmol/L saved for {user.username}"))

        except CustomUser.DoesNotExist:
            self.stderr.write(
                self.style.WARNING(f"Пристрій з ID '{device_sn}' не знайдено в базі!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))

