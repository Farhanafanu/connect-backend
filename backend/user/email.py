from django.core.mail import send_mail
from django.conf import settings
import random
from .models import *

def send_otp_email(email):
    subject = 'Your OTP for Login'
    otp = random.randint(10000,99999)
    message = f'Your OTP is: {otp}'
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [email])
    user_obj = CustomUser.objects.get(email = email)
    user_obj.otp = otp
    user_obj.save()