from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def auth_medic(request):
    return render(request, "authform_medic.html")
