from django import forms
from django.core.exceptions import ValidationError
from .models import Account

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Nhập mật khẩu',
        'class': 'form-control',
    }))

    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Nhập lại mật khẩu',
    }))


    class Meta:
        model = Account
        fields = ['first_name', 'last_name','phone_number', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            self.add_error('confirm_password', 'Mật khẩu không khớp!')
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise ValidationError("Email này đã được sử dụng!")
        return email


    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        # self.fields['first_name'].widget.attrs['placeholder'] = 'Nhập họ'
        # self.fields['last_name'].widget.attrs['placeholder'] = 'Nhập tên'
        # self.fields['phone_number'].widget.attrs['placeholder'] = 'Nhập số điện thoại'
        # self.fields['email'].widget.attrs['placeholder'] = 'Nhập email'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={'invalid': "Image files only"},widget=forms.FileInput(attrs={'class':'form-control'}))
    class Meta:
        model = Account
        fields = ('address_line_1', 'city', 'state', 'profile_picture')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'



