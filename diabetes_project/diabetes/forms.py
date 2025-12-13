from django import forms
from django.contrib.auth import get_user_model
#creating forms

CustomUser = get_user_model()

class AuthMedicForm(forms.Form):
    username = forms.CharField(label='Enter name', max_length=25)
    password = forms.CharField(label='Enter password', max_length=30, widget=forms.PasswordInput)

class RegisterMedicForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'hospital')

    username = forms.CharField(label="Enter name", max_length=25)
    email = forms.EmailField(label='Enter email', max_length=50)
    password = forms.CharField(label='Enter password', max_length=30)