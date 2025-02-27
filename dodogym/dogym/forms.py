from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import *

class StaffRegistrationForm(forms.Form):
    username = forms.CharField(label='ชื่อผู้ใช้', max_length=150)
    first_name = forms.CharField(label='ชื่อจริง', max_length=150)
    last_name = forms.CharField(label='นามสกุล', max_length=150)
    email = forms.EmailField(label='อีเมล')
    phone_number = forms.CharField(label='เบอร์โทรศัพท์', max_length=15)
    password1 = forms.CharField(label='รหัสผ่าน', widget=forms.PasswordInput)
    password2 = forms.CharField(label='ยืนยันรหัสผ่าน', widget=forms.PasswordInput)
    is_admin = forms.BooleanField(label='เป็นผู้ดูแลระบบ', required=False)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('ชื่อผู้ใช้นี้ถูกใช้งานแล้ว')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('อีเมลนี้ถูกใช้งานแล้ว')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'รหัสผ่านไม่ตรงกัน')

        return cleaned_data


class MemberRegistrationForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'id_card', 'birth_date', 'gender', 'weight', 'height', 'phone_number']

