from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)
