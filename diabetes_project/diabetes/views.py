from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.messages import get_messages
from .forms import *
from django.shortcuts import redirect
# Create your views here.
from django.contrib.auth.models import Group

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
    return user.groups.filter(name='Medic').exists()

def is_patient(user):
    return user.groups.filter(name='Patient').exists()


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

def register_medic(request):
    clear_messages(request)
    if request.user.is_authenticated:
        return redirect("/main_medic_page")

    if request.method == "POST":
        form = RegisterMedicForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
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
    clear_messages(request)
    if request.user.is_authenticated:
        if is_medic(request.user):
            return redirect('/main_medic_page')
        elif is_patient(request.user):
            return redirect('/auth_patient')
    return render(request, "main_page.html")

def main_medic_page(request):
    if not request.user.is_authenticated or not is_medic(request.user):
        return redirect('/auth_medic')

    patients = User.objects.filter(medic=request.user.username, groups__name="Patient")
    data = {
        "user": request.user,
        'patients': patients,
    }

    return render(request, "main_medic_page.html", context=data)

