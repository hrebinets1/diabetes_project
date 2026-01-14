import json
from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta
from .analysis import analyze_glucose_data
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

    patients = User.objects.filter(medic=request.user.username, role="patient")
    data = {
        "user": request.user,
        'patients': patients,
        "classification": classification_method(patients_dataset=""),
    }

    return render(request, "main_medic_page.html", context=data)


def main_patient_page(request):
    clear_messages(request)
    if not request.user.is_authenticated or not is_patient(request.user):
        return redirect('/auth_patient')
    if request.method == "POST":
        form = GlucoStatsForm(request.POST)
        if form.is_valid():
            reading = form.save(commit=False)
            reading.user = request.user
            reading.source = 'manual'
            reading.save()
            messages.success(request, "Показник успішно додано!")
            return redirect('/main_patient_page')
        else:
            messages.error(request, "Помилка при додаванні даних")
    else:
        form = GlucoStatsForm()

        # період та історія вимірювань
    period_key = request.GET.get('period', 'week')
    periods_map = {'day': 1, 'week': 7, 'month': 30, '3months': 90, 'year': 365}
    days = periods_map.get(period_key, 7)

    start_date = timezone.now() - timedelta(days=days)
    queryset = GlucoStats.objects.filter(
        user=request.user,
        measurement_date__gte=start_date
    ).order_by('measurement_date')

    last_record = GlucoStats.objects.filter(user=request.user).order_by('-measurement_date').first()
    current_level = float(last_record.level) if last_record else 0

    analysis = analyze_glucose_data(queryset, period_days=days)

    chart_history_json = "[]"
    stats_context = {}

    if analysis:
        stats_context = analysis['stats']
        chart_history_json = json.dumps(analysis['history'])

    context = {
        "user": request.user,
        "form": form,
        "current_level": current_level,
        "period": period_key,
        # Дані для графіків
        "history_data": chart_history_json,

        **stats_context #розпаковка статитстики
    }

    return render(request, "main_patient_page.html", context=context)