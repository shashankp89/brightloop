from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from core.permissions import role_required

from .forms import SignupForm, StaffCreateForm
from .models import User


def signup(request):
    if request.user.is_authenticated:
        return redirect("core:home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("core:home")
    return render(request, "accounts/signup.html", {"form": form})


@role_required(User.Role.ADMIN)
def staff_list(request):
    members = User.objects.exclude(role=User.Role.CUSTOMER)
    return render(request, "accounts/staff_list.html", {"members": members})


@role_required(User.Role.ADMIN)
def staff_create(request):
    form = StaffCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        member = form.save()
        messages.success(request, f"{member.name} can now sign in as staff.")
        return redirect("accounts:staff_list")
    return render(request, "accounts/staff_form.html", {"form": form})
