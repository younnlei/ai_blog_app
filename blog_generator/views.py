from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return render(request, 'index.html')

def user_login(request):
    return render(request, 'login.html')

def user_signup(request):
    return render(request, 'signup.html')

def user_logout(request):
    return render(request, 'signup.html')