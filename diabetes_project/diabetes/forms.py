from django import forms
from django.contrib.auth import get_user_model
#creating forms

CustomUser = get_user_model()

class AuthMedicForm(forms.Form):
    username = forms.CharField(label="Впишіть ім'я", max_length=25)
    password = forms.CharField(label="Впишіть пароль", max_length=30, widget=forms.PasswordInput)

class AuthPatientForm(forms.Form):
    username = forms.CharField(label="Впишіть ім'я", max_length=25)
    password = forms.CharField(label="Впишіть пароль", max_length=30, widget=forms.PasswordInput)


class RegisterMedicForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'hospital')
        labels = {
            'first_name': "Ваше ім'я",
            'last_name': "Ваше прізвище",
            'hospital': "Ваша лікарня"
        }

    username = forms.CharField(label="Впишіть логін", max_length=25)
    email = forms.EmailField(label='Впишіть пошту', max_length=50)
    password = forms.CharField(label='Впишіть пароль', max_length=30)


class RegisterPatientForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'diabetes', 'medic')
        labels = {
            'first_name': "Ваше ім'я",
            'last_name': "Ваше прізвище",
            'diabetes': "Тип діабету",
            'medic': "Лікар"
        }
        widgets = {
            'password': forms.PasswordInput()
        }

    username = forms.CharField(label="Впишіть логін", max_length=25)
    email = forms.EmailField(label='Впишіть пошту', max_length=50)
    password = forms.CharField(label='Впишіть пароль', max_length=30, widget=forms.PasswordInput)

