from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import *
from django.shortcuts import redirect
# Create your views here.
from django.contrib.auth.models import Group

def auth_medic(request):
    if request.method == "POST":
        form = AuthMedicForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Correct information! Login...")
                return redirect("/")
            else:
                messages.error(request, "Incorrect information! Try again...")

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

    return render(request, "main_page.html")

def main_medic_page(request):

    return render(request, "main_medic_page.html")
