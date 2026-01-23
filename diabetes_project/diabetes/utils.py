import random
from datetime import timedelta
from django.utils import timezone
from .models import GlucoStats, ActivityEvent, MedicationEvent, MealEvent


def generate_cgm_data(user, days=30):

    end_time = timezone.now()
    start_time = end_time - timedelta(days=days)

    stats = []
    current_time = start_time
    meal_windows = {
        'breakfast': (7, 9, 0.25),
        'lunch': (12, 14, 0.25),
        'dinner': (19, 21, 0.25)
    }
    base_level = 4.8
    trend = 0

    meal_effect_timer = 0  # ітерацій (по 15 хв), поки діє ефект їжі
    meds_effect_timer = 0  # ітерацій, поки діє ефект ліків

    meals_eaten = {'breakfast': False, 'lunch': False, 'dinner': False}
    last_day = current_time.day

    while current_time <= end_time:

        if current_time.day != last_day:
            meals_eaten = {'breakfast': False, 'lunch': False, 'dinner': False}
            last_day = current_time.day

        hour = current_time.hour

        # Перевірка на прийом їжі
        chosen_meal = None
        for meal_name, (start_h, end_h, prob) in meal_windows.items():
            if start_h <= hour < end_h and not meals_eaten[meal_name]:
                # Шанс поїсти в цей проміжок часу
                if random.random() < prob:
                    chosen_meal = meal_name
                    meals_eaten[meal_name] = True
                    break

        # Якщо їмо
        if chosen_meal:
            carbs = random.randint(30, 100)

            MealEvent.objects.create(
                user=user,
                timestamp=current_time,
                meal_type=chosen_meal.capitalize(),
                carbs=carbs,
                note="autogen"
            )

            # Їжа штовхає цукор вгору
            trend += (carbs / 40.0)
            meal_effect_timer = 12

        # Якщо цукор високий (> 10) і тренд росте або стабільний >> прийом інсуліну
        if base_level > 10.0 and trend > -0.1:
            dosage = random.randint(2, 6)
            MedicationEvent.objects.create(
                user=user,
                timestamp=current_time,
                medicine_name="Інсулін",
                dosage=dosage,
                note="Корекція"
            )
            # Інсулін штовхає тренд різко вниз
            trend -= (dosage * 0.4)
            meds_effect_timer = 16

        # Активність
        if 18 <= hour <= 21 and random.random() < 0.05 and trend > -0.2:
            duration = 30
            ActivityEvent.objects.create(
                user=user,
                timestamp=current_time,
                activity_type="Прогулянка",
                duration_minutes=duration,
                note="Вечірня активність"
            )
            trend -= 0.5

        # Якщо цукор високий, організм намагається його трохи знизити сам, і навпаки
        target_level = 4.8
        diff = base_level - target_level
        trend -= diff * 0.03  #

        # Затухання інерції
        trend *= 0.85

        noise = random.uniform(-0.03, 0.03)
        base_level += trend + noise

        if base_level > 14.0:
            trend -= 0.2
            base_level = min(base_level, 16.0)  # Абсолютний пік

        if base_level < 3.0:
            trend += 0.15
            base_level = max(base_level, 2.0)  # Абсолютне дно

        save_level = round(base_level, 2)

        if meds_effect_timer > 0:
            context = 'post_meds'
        elif meal_effect_timer > 0:
            context = 'post_meal'
        else:
            context = 'normal'

        if meal_effect_timer > 0: meal_effect_timer -= 1
        if meds_effect_timer > 0: meds_effect_timer -= 1

        stats.append(GlucoStats(
            user=user,
            level=save_level,
            measurement_date=current_time,
            source='auto',
            context=context
        ))

        if len(stats) >= 500:
            GlucoStats.objects.bulk_create(stats)
            stats = []

        current_time += timedelta(minutes=15)

        # Записуємо залишок
    if stats:
        GlucoStats.objects.bulk_create(stats)