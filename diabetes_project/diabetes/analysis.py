from datetime import timedelta

import pandas as pd
import numpy as np
from django.utils import timezone

from sklearn.linear_model import LinearRegression
from .models import MealEvent, MedicationEvent, ActivityEvent

def analyze_glucose_data(user, queryset, period_days=30):

    start_date = timezone.now() - timedelta(days=period_days)

    data = list(queryset.values('measurement_date', 'level'))

    if not data or len(data) < 2:
        return {
            'stats': {'avg': 0, 'min': 0, 'max': 0, 'hba1c': 0},
            'history': [],
            'events': []
        }

    df = pd.DataFrame(data)
    df['level'] = df['level'].astype(float)
    df['measurement_date'] = pd.to_datetime(df['measurement_date'])


    mean_val = df['level'].mean()
    stats = {
        'avg': round(mean_val, 1),
        'min': round(df['level'].min(), 1),
        'max': round(df['level'].max(), 1),
        'hba1c': round((mean_val + 2.59) / 1.59, 1) # глікований гемоглобін
    }

    # Агрегація історії для графіка
    if period_days > 7:
        df_resampled = df.set_index('measurement_date').resample('D').mean().dropna()
        history_data = [
            {
                'x': d.date().isoformat(),
                'y': round(value, 2)
            }
            for d, value in zip(df_resampled.index, df_resampled['level'])
        ]
        is_aggregated = True
    else:
        history_data = [
            {
                'x': date.isoformat(),
                'y': round(value, 2)
            }
            for date, value in zip(df['measurement_date'], df['level'])
        ]
        is_aggregated = False

    events_data = []

    meals = list(MealEvent.objects.filter(user=user, timestamp__gte=start_date)
                 .values('timestamp', 'meal_type', 'carbs'))
    meds = list(MedicationEvent.objects.filter(user=user, timestamp__gte=start_date)
                .values('timestamp', 'medicine_name', 'dosage'))
    acts = list(ActivityEvent.objects.filter(user=user, timestamp__gte=start_date)
                .values('timestamp', 'activity_type', 'duration_minutes'))

    if is_aggregated:
        if meals:
            m_df = pd.DataFrame(meals)
            m_df['date'] = pd.to_datetime(m_df['timestamp']).dt.date
            m_agg = m_df.groupby('date').agg( #Сума вуглеводів за день
                count=('timestamp', 'size'),
                total_carbs=('carbs', 'sum')
            )
            for date, row in m_agg.iterrows():
                events_data.append({
                    'x': date.isoformat(),
                    'y': 3,
                    'title': f"meal Їжа (x{int(row['count'])})",
                    'desc': f"Всього за добу: {int(row['total_carbs'])}г вугл."
                })

        if meds:
            med_df = pd.DataFrame(meds)
            med_df['date'] = pd.to_datetime(med_df['timestamp']).dt.date
            med_df['dosage_num'] = pd.to_numeric(med_df['dosage']).fillna(0)

            med_agg = med_df.groupby('date').agg( #Сума ліків за день
                count=('timestamp', 'size'),
                total_dosage=('dosage_num', 'sum')
            )
            for date, row in med_agg.iterrows():
                dosage_str = f"{row['total_dosage']}" if row['total_dosage'] > 0 else "вказано текстом"
                events_data.append({
                    'x': date.isoformat(),
                    'y': 2.5,
                    'title': f"med Ліки (x{int(row['count'])})",
                    'desc': f"Загальна доза: {dosage_str}"
                })

        if acts:
            act_df = pd.DataFrame(acts)
            act_df['date'] = pd.to_datetime(act_df['timestamp']).dt.date
            act_agg = act_df.groupby('date').agg( #Сума активності за день
                count=('timestamp', 'size'),
                total_min=('duration_minutes', 'sum')
            )
            for date, row in act_agg.iterrows():
                events_data.append({
                    'x': date.isoformat(),
                    'y': 2,
                    'title': f"act Спорт (x{int(row['count'])})",
                    'desc': f"Активність: {int(row['total_min'])} хв за день"
                })
    else:

        meals = MealEvent.objects.filter(user=user, timestamp__gte=start_date).order_by('-timestamp')
        for m in meals:
            events_data.append({
                'x': m.timestamp.isoformat(),
                'y': 3,
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


def get_forecast_and_recommendations(user, queryset, period_days):
    if queryset.count() < 10: return None

    data = list(queryset.values('measurement_date', 'level'))
    df = pd.DataFrame(data)
    df['level'] = df['level'].astype(float)
    df['measurement_date'] = pd.to_datetime(df['measurement_date'])

    # Для довгих прогнозів працюємо з середньоденними значеннями
    if period_days > 7:
        df_daily = df.set_index('measurement_date').resample('D').mean().dropna().reset_index()
        df_daily['ts'] = df_daily['measurement_date'].apply(lambda x: x.timestamp())
        X = df_daily[['ts']].values
        y = df_daily['level'].values
        last_val = y[-1]
        last_ts = df_daily['ts'].max()
    else:
        df['ts'] = df['measurement_date'].apply(lambda x: x.timestamp())
        X = df[['ts']].values
        y = df['level'].values
        last_val = y[-1]
        last_ts = df['ts'].max()

    model = LinearRegression().fit(X, y)

    # Прогноз
    num_points = 30 if period_days > 7 else 24
    future_ts = np.linspace(last_ts, last_ts + (period_days * 24 * 3600), num=num_points)
    future_preds = model.predict(future_ts.reshape(-1, 1))

    # Вирівнювання прогноз починався з останньої точки
    gap = last_val - future_preds[0]

    forecast_points = []
    for i, (ts, pred) in enumerate(zip(future_ts, future_preds)):
        dt = timezone.datetime.fromtimestamp(ts)
        smooth_val = pred + (gap * max(0, 1 - i / (num_points / 2)))
        forecast_points.append({'x': dt.isoformat(), 'y': round(max(2, min(smooth_val, 25)), 2)})

    return {
        'points': forecast_points,
        'recommendations': ["Тренд: Аналіз показує поступове зниження середньоденного рівня."
                            if model.coef_[0] < 0 else "Тренд: Спостерігається тенденція до зростання середнього показника."]
    }