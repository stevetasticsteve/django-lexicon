from django.shortcuts import render


def home(request):
    return render(request, template_name="home.html")


def to_do(request):
    return render(request, template_name="to_do.html")
