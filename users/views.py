from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def register_view(request):
    """
    Foydalanuvchini ro'yxatdan o'tkazish.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Oddiy validatsiyalar
        if password1 != password2:
            messages.error(request, "Parollar bir xil emas.")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu username allaqachon mavjud.")
            return redirect('register')

        # User yaratamiz
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        messages.success(request, "Ro'yxatdan o'tish muvaffaqiyatli bo'ldi. Endi tizimga kiring.")
        return redirect('login')

    return render(request, 'users/register.html')


def login_view(request):
    """
    Foydalanuvchini tizimga kiritish.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Tizimga muvaffaqiyatli kirdingiz.")
            return redirect('home')
        else:
            messages.error(request, "Username yoki parol noto'g'ri.")
            return redirect('login')

    return render(request, 'users/login.html')


def logout_view(request):
    """
    Foydalanuvchini tizimdan chiqarish.
    """
    logout(request)
    messages.success(request, "Tizimdan chiqdingiz.")
    return redirect('home')