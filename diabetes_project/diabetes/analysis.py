from datetime import timedelta

import pandas as pd
import numpy as np
from django.utils import timezone

from .models import MealEvent, MedicationEvent, ActivityEvent


def analyze_glucose_data(user, queryset, period_days=30):

    start_date = timezone.now() - timedelta(days=period_days)

    data = list(queryset.values('measurement_date', 'level'))

    if not data:
        return {
            'stats': {'avg': 0, 'min': 0, 'max': 0, 'hba1c': 0},
            'history': [],
            'events':[]
            ####'forecast': []
        }

    df = pd.DataFrame(data)
    df['level'] = df['level'].astype(float)
    df['measurement_date'] = pd.to_datetime(df['measurement_date'])
    df.set_index('measurement_date', inplace=True)
    df.sort_index(inplace=True)  #  від старих до нових

    if period_days > 90:

        df_resampled = df.resample('D').mean().dropna()
    else:

        df_resampled = df

    # Розрахунок статистики
    mean_val = df['level'].mean()
    stats = {
        'avg': round(mean_val, 1),
        'min': round(df['level'].min(), 1),
        'max': round(df['level'].max(), 1),
        'hba1c': round((mean_val + 2.59) / 1.59, 1) # глікований гемоглобін
    }

    history_data = [
        {
            'x': date.isoformat(),
            'y': round(value, 2)
        }
        for date, value in zip(df_resampled.index, df_resampled['level'])
    ]
    events_data = []

    meals = MealEvent.objects.filter(user=user, timestamp__gte=start_date).order_by('-timestamp')
    for m in meals:
        events_data.append({
            'x': m.timestamp.isoformat(),
            'y': 3,  # Візуальна висота на графіку
            'title': f"meal {m.meal_type}",
            'desc': f"{m.carbs}г вугл. {m.note}"
        })

    meds = MedicationEvent.objects.filter(user=user, timestamp__gte=start_date).order_by('-timestamp')
    for med in meds:
        events_data.append({
            'x': med.timestamp.isoformat(),
            'y': 2.5,
            'title': f"med {med.medicine_name}",
            'desc': f"Доза: {med.dosage}. {med.note}"
        })

    acts = ActivityEvent.objects.filter(user=user, timestamp__gte=start_date).order_by('-timestamp')
    for act in acts:
        events_data.append({
            'x': act.timestamp.isoformat(),
            'y': 2,
            'title': f"act {act.activity_type}",
            'desc': f"{act.duration_minutes} хв. {act.note}"
        })

    return {
        'stats': stats,
        'history': history_data,
        'events': events_data
        ######'forecast': []
    }


def calculate_current_status(level, context, diabetes_type):

    level = float(level)


    hypo_threshold = 3.9

    if context in ['post_meal', 'post_meds']:
        target_max = 10.0
        high_threshold = 13.0
    else:
        # Натще або в звичайному стані
        target_max = 7.0
        high_threshold = 10.0

    # гіпоглікемія
    if level < hypo_threshold:
        return {
            'status': 'Гіпоглікемія',
            'color': 'Red',
            'bg_color': '#fadbd8',
            'message': 'Рівень небезпечно низький! Вживіть швидкі вуглеводи (сік, цукор).'
        }

    # Норма
    elif hypo_threshold <= level <= target_max:
        return {
            'status': 'В нормі',
            'color': 'Green',
            'bg_color': '#d7fce7',
            'message': 'Показники в межах цільового діапазону.'
        }

    # Підвищений
    elif target_max < level <= high_threshold:
        return {
            'status': 'Підвищений',
            'color': '#d15502',
            'bg_color': '#ffd9bf',
            'message': 'Рівень вище цільового. Слідкуйте за динамікою.'
        }

    # Гіперглікемія
    else:

        msg = 'Високий ризик! Перевірте кетони та скоригуйте інсулін.' if diabetes_type == 'type1' else 'Рівень значно перевищує норму. Зверніть увагу на дієту/ліки.'

        return {
            'status': 'Гіперглікемія',
            'color': '#750202',  # Dark Red
            'bg_color': '#e3b6b6',
            'message': msg
        }