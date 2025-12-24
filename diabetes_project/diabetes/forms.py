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
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'hospital', 'position')
        labels = {
            'first_name': "Ваше ім'я",
            'last_name': "Ваше прізвище",
            'hospital': "Ваша лікарня",
            'position': "Ваша посада",
        }

    username = forms.CharField(label="Впишіть логін", max_length=25)
    email = forms.EmailField(label='Впишіть пошту', max_length=50)
    password = forms.CharField(label='Впишіть пароль', max_length=30)


class RegisterPatientForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'diabetes', 'medic','hospital')
        labels = {
            'first_name': "Ваше ім'я",
            'last_name': "Ваше прізвище",
            'diabetes': "Тип діабету",
            'medic': "Лікар",
            'hospital': "Лікарня"
        }
        widgets = {
            'password': forms.PasswordInput()
        }

    username = forms.CharField(label="Впишіть логін", max_length=25)
    email = forms.EmailField(label='Впишіть пошту', max_length=50)
    password = forms.CharField(label='Впишіть пароль', max_length=30, widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Підтвердіть пароль', max_length=30, widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Паролі не співпадають!")

        return cleaned_data

    def clean_medic(self):
        medic_username = self.cleaned_data.get('medic')
        if medic_username:
            try:
                medic = CustomUser.objects.get(username=medic_username, role='medic')
            except CustomUser.DoesNotExist:
                raise forms.ValidationError("Лікар з таким username не знайдений!")
        return medic_username

