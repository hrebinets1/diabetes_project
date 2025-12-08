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

def is_member(user, name):
    return user.groups.filter(name=name).exists()

def auth_medic(request):
    if request.method == "POST":
        form = AuthMedicForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and is_member(user, 'Medic'):
                login(request, user)
                messages.success(request, "Correct information! Login...")
                return redirect("/main_medic_page/")
            else:
                messages.error(request, "Incorrect information! Try again...")
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
            messages.success(request, "Registration successful")
            return redirect("/")
    else:
        form = RegisterMedicForm()
    return render(request, "register_medic.html", { 'form': form } )

def auth_patient(request):
    return render(request, "auth_patient.html")

def main_page(request):
    context = {
        'user': request.user,
    }
    return render(request, "main_page.html", context)

def main_medic_page(request):
    data = {
        "username": request.user.username,
    }
    if not request.user.is_authenticated or not is_member(request.user, 'Medic'):
        return redirect('/auth_medic')
    return render(request, "main_medic_page.html", context=data)
