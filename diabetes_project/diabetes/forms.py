from django import forms
from django.contrib.auth.models import User
#creating forms

class AuthMedicForm(forms.Form):
    username = forms.CharField(label='Enter name', max_length=25)
    password = forms.CharField(label='Enter password', max_length=30, widget=forms.PasswordInput)

class RegisterMedicForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')


    username = forms.CharField(label="Enter name", max_length=25)
    email = forms.EmailField(label='Enter email', max_length=50)
    password = forms.CharField(label='Enter password', max_length=30)