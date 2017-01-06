import uuid
import sys
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.core.mail import send_mail

from accounts.models import Token
import logging

def send_login_email(request):
    email = request.POST['email']
    send_mail(
        'Your login link for Superlists',
        'body text tbc',
        'noreply@superlists',
        [email])
    return redirect('/')
