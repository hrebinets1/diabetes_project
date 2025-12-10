from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import *
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
# Create your views here.
from django.contrib.auth.models import Group


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect("/")


def is_medic(user):
    return user.groups.filter(name='Medic').exists()

def is_patient(user):
    return user.groups.filter(name='Patient').exists()


def auth_medic(request):
    if request.method == "POST":
        form = AuthMedicForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and is_medic(user):
                login(request, user)
                return redirect("/main_medic_page/")
            else:
                form = AuthMedicForm()

    else:
        form = AuthMedicForm()

    return render(request, "auth_medic.html", { 'form': form })

def register_medic(request):
    if request.method == "POST":
        form = RegisterMedicForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.save()
            medic_group = Group.objects.get(name='Medic')
            new_user.groups.add(medic_group)
            login(request, new_user)
            return redirect("/main_medic_page")
    else:
        form = RegisterMedicForm()
    return render(request, "register_medic.html", { 'form': form } )

def auth_patient(request):
    return render(request, "auth_patient.html")

def main_page(request):
    if request.user.is_authenticated:
        if is_medic(request.user):
            return redirect('/main_medic_page')
        elif is_patient(request.user):
            return redirect('/auth_patient')
    return render(request, "main_page.html")

def main_medic_page(request):
    data = {
        "username": request.user.username,
    }
    if not request.user.is_authenticated or not is_medic(request.user):
        return redirect('/auth_medic')
    return render(request, "main_medic_page.html", context=data)

