import random
from datetime import timedelta
from django.utils import timezone
from .models import GlucoStats


def generate_cgm_data(user, days=7):

    end_time = timezone.now()
    start_time = end_time - timedelta(days=days)

    stats = []
    current_time = start_time

    while current_time <= end_time:

        hour = current_time.hour
        base_level = 5.5

        # Імітація їжі
        # Сніданок (7-9), Обід (12-14), Вечеря (19-21)
        meal_spike = 0
        if 8 <= hour < 10:
            meal_spike = random.uniform(1.5, 3.5)  # Сніданок
        elif 13 <= hour < 15:
            meal_spike = random.uniform(2.0, 4.0)  # Обід
        elif 19 <= hour < 21:
            meal_spike = random.uniform(1.5, 3.0)  # Вечеря

        # Рандомізація
        final_level = base_level + meal_spike + random.uniform(-0.2, 0.2)

        # Межі
        final_level = round(max(3.0, min(17.0, final_level)), 1)

        stats.append(GlucoStats(
            user=user,
            level=final_level,
            measurement_date=current_time,
            source='auto',
            notes='CGM Simulation'
        ))

        # крок вимірювання
        current_time += timedelta(minutes=7)

    GlucoStats.objects.bulk_create(stats)
