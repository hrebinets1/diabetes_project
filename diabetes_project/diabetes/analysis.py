import pandas as pd
import numpy as np
from .models import MealEvent, MedicationEvent, ActivityEvent


def analyze_glucose_data(user, queryset, period_days=30):

    data = list(queryset.values('measurement_date', 'level'))

    if not data:
        return {
            'stats': {'avg': 0, 'min': 0, 'max': 0, 'hba1c': 0},
            'history': [],
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

    meals = MealEvent.objects.filter(user=user).order_by('-timestamp')[:50]
    for m in meals:
        events_data.append({
            'x': m.timestamp.isoformat(),
            'y': 3,  # Візуальна висота на графіку
            'title': f"meal {m.meal_type}",
            'desc': f"{m.carbs}г вугл. {m.note}"
        })

    meds = MedicationEvent.objects.filter(user=user).order_by('-timestamp')[:50]
    for med in meds:
        events_data.append({
            'x': med.timestamp.isoformat(),
            'y': 2.5,
            'title': f"med {med.medicine_name}",
            'desc': f"Доза: {med.dosage}. {med.note}"
        })

    acts = ActivityEvent.objects.filter(user=user).order_by('-timestamp')[:50]
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