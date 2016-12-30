import uuid
import sys
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.core.mail import send_mail

from accounts.models import Token
import logging

def send_login_email(request):
    logging.warning("in send login email")
    email = request.POST['email']
    uid = str(uuid.uuid4())
    Token.objects.create(email=email, uid=uid)
    print('saving uid', uid, 'for email', email, file=sys.stderr)
    url = request.build_absolute_uri(
        '/accounts/login?uid={uid}'.format(uid=uid)
    )
    send_mail(
        'Your login link for Superlists',
        'Use this link to log in:\n\n{url}'.format(url=url),
        'noreply@gmail.com',
        [email],
    )
    return render(request, 'login_email_sent.html')


def login(request):
    logging.warning("in login")
    print('login view', file=sys.stderr)
    uid = request.GET.get('uid')
    user = authenticate(uid=uid)
    if user is not None:
        auth_login(request, user)
    return redirect('/')

def logout(request):
    logging.warning("in logout")
    auth_logout(request)
    return redirect('/')
