from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from users.forms import RegisterForm
from users.models import User


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_url = request.build_absolute_uri(
            reverse(
                "users:activate",
                kwargs={"uidb64": uid, "token": token},
            )
        )
        send_mail(
            subject="Подтверждение регистрации",
            message=(
                "Перейдите по ссылке для подтверждения email:\n"
                f"{activation_url}"
            ),
            from_email=None,
            recipient_list=[user.email],
        )
        return render(
            request,
            "users/message.html",
            {"message": "Письмо с подтверждением отправлено."},
        )

    return render(
        request,
        "users/form.html",
        {"form": form, "title": "Регистрация"},
    )


def activate(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save(update_fields=("is_active",))
        messages.success(request, "Email подтверждён. Можно войти.")
        return redirect("users:login")

    return render(
        request,
        "users/message.html",
        {"message": "Ссылка подтверждения недействительна."},
        status=400,
    )