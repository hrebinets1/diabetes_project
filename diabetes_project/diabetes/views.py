import json
import joblib

from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta
from .analysis import analyze_glucose_data, calculate_current_status, get_forecast_and_recommendations
from .forms import *
from django.shortcuts import redirect
from .analysis_medic import classification_method
from .utils import generate_cgm_data


User = get_user_model()

# щоб в html формі не виводилися повідомлення з інших форм
def clear_messages(request):
    storage = get_messages(request)
    for msg in storage:
        pass

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        clear_messages(request)
        messages.success(request, "Logout success")
    return redirect("/")

def is_medic(user):
    return getattr(user, 'role', None) == 'medic'

def is_patient(user):
    return getattr(user, 'role', None) == 'patient'


def auth_medic(request):
    clear_messages(request)
    if request.user.is_authenticated:
        return redirect("/main_medic_page")

    if request.method == "POST":
        form = AuthMedicForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and is_medic(user):
                login(request, user)
                messages.success(request, "Success!.")
                return redirect("/main_medic_page/")
            else:
                form = AuthMedicForm()
                messages.error(request, "Error during authorization!")

    else:
        form = AuthMedicForm()

    return render(request, "auth_medic.html", { 'form': form })

def auth_patient(request):
    clear_messages(request)
    if request.user.is_authenticated:
        return redirect("/main_patient_page")

    if request.method == "POST":
        form = AuthPatientForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and is_patient(user):
                login(request, user)
                messages.success(request, "Success!")
                return redirect("/main_patient_page/")
            else:
                form = AuthPatientForm()
                messages.error(request, "Помилка авторизації!")
    else:
        form = AuthPatientForm()

    return render(request, "auth_patient.html", {'form': form})

def register_medic(request):
    clear_messages(request)
    if request.user.is_authenticated:
        return redirect("/main_medic_page")

    if request.method == "POST":
        form = RegisterMedicForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.role = 'medic'
            new_user.save()
            login(request, new_user)
            return redirect("/main_medic_page")
    else:
        form = RegisterMedicForm()
    return render(request, "register_medic.html", { 'form': form } )

def register_patient(request):
    clear_messages(request)
    if request.user.is_authenticated:
        return redirect("/main_patient_page")

    if request.method == "POST":
        form = RegisterPatientForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.role = 'patient'
            new_user.save()
            generate_cgm_data(new_user, days=30)
            login(request, new_user)
            messages.success(request, "Реєстрація успішна!")
            return redirect("/main_patient_page")
    else:
        form = RegisterPatientForm()

    return render(request, "register_patient.html", {'form': form})


def main_page(request):
    clear_messages(request)
    if request.user.is_authenticated:
        if is_medic(request.user):
            return redirect('/main_medic_page')
        elif is_patient(request.user):
            return redirect('/main_patient_page')
    return render(request, "main_page.html")

def main_medic_page(request):
    if not request.user.is_authenticated or not is_medic(request.user):
        return redirect('/auth_medic')

    patients_list = User.objects.filter(medic=request.user.username, role="patient")

    patients_data_for_template = []

    for patient in patients_list:
        #класифікація за останнім введеним показником
        last_record = GlucoStats.objects.filter(user=patient).order_by('-measurement_date').first()
        #значення за замовчуванням
        classification_status = "Немає даних"
        hba1c_val = "-"
        CONTEXT_DISPLAY = {
            'normal': 'Натщесерце',
            'post_meal': 'Після їжі',
            'post_meds': 'Після ліків',
            'post_exercise': 'Після активності'
        }

        if last_record:
            current_level = float(last_record.level)
            hba1c_val = round((current_level + 2.59) / 1.59, 1)
            #перетворення даних з БД для класифікації
            context_map = {'normal': 0, 'post_meal': 1, 'post_meds': 2, 'post_exercise': 3}
            ctx_code = context_map.get(last_record.context.lower())

            type_map = {'type1': 1, 'type2': 2}
            type_code = type_map.get(getattr(patient, 'diabetes').lower())
            #Класифікація пацієнта з використанням scikit-learn
            model_features = [[current_level, hba1c_val, ctx_code, type_code]]
            loaded_model = joblib.load(
                open("diabetes/clf_model.pkl", 'rb')
            )
            classification_status = loaded_model.predict(model_features)[0]

        database_context = last_record.context if last_record else "—"

        if database_context in CONTEXT_DISPLAY:
            current_context = CONTEXT_DISPLAY[database_context]
        else:
            current_context = '-'

        diabetes_type = getattr(patient, 'diabetes')
        patients_data_for_template.append({
            'profile': patient,
            'last_glucose': last_record.level if last_record else "—",
            'hba1c': hba1c_val,
            'classification_status': classification_status,
            'last_update': last_record.measurement_date if last_record else None,
            'context_display': current_context,
            'diabetes_type': diabetes_type
        })

    data = {
        "user": request.user,
        "patients": patients_data_for_template,
    }

    return render(request, "main_medic_page.html", context=data)


def main_patient_page(request):
    clear_messages(request)
    if not request.user.is_authenticated or not is_patient(request.user):
        return redirect('/auth_patient')

    forms_dict = {
        'gluco_form': GlucoStatsForm(prefix='gluco'),
        'meal_form': MealEventForm(prefix='meal'),
        'meds_form': MedicationEventForm(prefix='meds'),
        'activity_form': ActivityEventForm(prefix='act'),
    }

    if request.method == "POST":
        if 'submit_gluco' in request.POST:
            form = GlucoStatsForm(request.POST, prefix='gluco')
            if form.is_valid():
                stat = form.save(commit=False)
                stat.user = request.user
                stat.source = 'manual'
                stat.save()
                messages.success(request, "Показник успішно додано!")
                return redirect('/main_patient_page')
            else:
                forms_dict['gluco_form'] = form
                messages.error(request, "Помилка при додаванні даних")

        elif 'submit_meal' in request.POST:
            form = MealEventForm(request.POST, prefix='meal')
            if form.is_valid():
                meal = form.save(commit=False)
                meal.user = request.user
                meal.save()
                messages.success(request, "Прийом їжі записано!")
                return redirect('/main_patient_page')

        elif 'submit_meds' in request.POST:
            form = MedicationEventForm(request.POST, prefix='meds')
            if form.is_valid():
                med = form.save(commit=False)
                med.user = request.user
                med.save()
                messages.success(request, "Прийом ліків записано!")
                return redirect('/main_patient_page')

        elif 'submit_act' in request.POST:
            form = ActivityEventForm(request.POST, prefix='act')
            if form.is_valid():
                act = form.save(commit=False)
                act.user = request.user
                act.save()
                messages.success(request, "Активність записано!")
                return redirect('/main_patient_page')


        # період та історія вимірювань
    period_key = request.GET.get('period', 'week')
    is_forecast_period = period_key.startswith('forecast_')
    periods_map = {'day': 1, 'week': 7, 'month': 30, '3months': 90, 'year': 365,
                   'forecast_month': 30, 'forecast_3months': 90, 'forecast_year': 365}
    days = periods_map.get(period_key, 7)
    show_forecast = is_forecast_period

    start_date = timezone.now() - timedelta(days=days)
    queryset = GlucoStats.objects.filter(
        user=request.user,
        measurement_date__gte=start_date
    ).order_by('measurement_date')

    last_record = GlucoStats.objects.filter(user=request.user).order_by('-measurement_date').first()
    current_level = 0
    status_info = {
        'status': 'Немає даних',
        'color': '#7f8c8d',
        'bg_color': '#ecf0f1',
        'message': 'Додайте вимірювання'
    }

    if last_record:
        current_level = float(last_record.level)
        status_info = calculate_current_status(
            level=current_level,
            context=last_record.context,
            diabetes_type=getattr(request.user, 'diabetes', 'type1')
        )

    analysis = analyze_glucose_data(request.user, queryset, period_days=days)

    chart_history_json = "[]"
    chart_events_json = "[]"
    stats_context = {}

    if analysis:
        stats_context = analysis['stats']
        chart_history_json = json.dumps(analysis['history'])
        chart_events_json = json.dumps(analysis['events'])

    forecast_json = "[]"
    recommendations = []

    if show_forecast:
        forecast_results = get_forecast_and_recommendations(request.user, queryset, period_days=days)
        if forecast_results:
            forecast_json = json.dumps(forecast_results['points'])
            recommendations = forecast_results['recommendations']

    context = {
        "user": request.user,
        "current_level": current_level,
        "status_info": status_info,
        "period": period_key,
        # Дані для графіків
        "history_data": chart_history_json,
        "events_data": chart_events_json,
        "show_forecast": show_forecast,
        "forecast_data": forecast_json,
        "recommendations": recommendations,
        **forms_dict,
        **stats_context #розпаковка статитстики
    }

    return render(request, "main_patient_page.html", context=context)