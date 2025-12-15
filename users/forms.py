from django import forms # type: ignore
from django.contrib.auth.forms import UserCreationForm # type: ignore
from .models import CustomUser

class BaseSignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role', "photo"]

class TransitorSignupForm(BaseSignupForm):
    transitor_license = forms.ImageField(required=True)
    job_title = forms.CharField(required=True)
    photo = forms.ImageField(required=False)
    business_card = forms.FileField(required=True)
    company_id_card = forms.FileField(required=False)
    tin_vat_number = forms.CharField(required=True)
    course_material = forms.FileField(required=False)


class InstructorSignupForm(BaseSignupForm):
    job_title = forms.CharField(required=True)
    certificate = forms.FileField(required=True)
    photo = forms.ImageField(required=False)
    years_of_experience = forms.IntegerField(required=True)
    course_title = forms.CharField(required=True)



class TaxWorkerSignupForm(BaseSignupForm):
    job_title = forms.CharField(required=True)
    organization_name = forms.CharField(required=True)
    photo = forms.ImageField(required=False)
    work_email = forms.EmailField(required=True)
    company_id_card = forms.FileField(required=True)
    phone_number = forms.CharField(required=False)
    years_of_experience = forms.IntegerField(required=True)


