from typing import Type

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Model, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from mailing.forms import MailingForm, MessageForm, RecipientForm
from mailing.models import Mailing, Message, Recipient
from mailing.services import send_mailing


def is_manager(user) -> bool:
    return user.groups.filter(name="Менеджеры").exists()


def visible_objects(model: Type[Model], user) -> QuerySet:
    queryset = model.objects.all()
    if is_manager(user):
        return queryset
    return queryset.filter(owner=user)


def clear_stats_cache() -> None:
    cache.clear()


@login_required
def home(request: HttpRequest) -> HttpResponse:
    cache_key = f"home-stats:{request.user.pk}:{int(is_manager(request.user))}"
    context = cache.get(cache_key)

    if context is None:
        mailings = visible_objects(Mailing, request.user)
        recipients = visible_objects(Recipient, request.user)
        context = {
            "total_mailings": mailings.count(),
            "active_mailings": mailings.filter(status=Mailing.STARTED).count(),
            "unique_recipients": recipients.count(),
        }
        cache.set(cache_key, context, timeout=60)

    return render(request, "mailing/home.html", context)


def edit_object(
    request: HttpRequest,
    *,
    model: Type[Model],
    form_class: Type[ModelForm],
    success_url: str,
    title: str,
    pk: int | None = None,
) -> HttpResponse:
    instance = None
    if pk is not None:
        instance = get_object_or_404(model, pk=pk, owner=request.user)

    kwargs = {
        "data": request.POST or None,
        "instance": instance,
    }
    if form_class is MailingForm:
        kwargs["user"] = request.user

    form = form_class(**kwargs)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if instance is None:
            obj.owner = request.user
        obj.save()
        form.save_m2m()
        clear_stats_cache()
        messages.success(request, "Изменения сохранены.")
        return redirect(success_url)

    return render(request, "mailing/form.html", {"form": form, "title": title})


def delete_object(
    request: HttpRequest,
    *,
    model: Type[Model],
    success_url: str,
    pk: int,
) -> HttpResponse:
    obj = get_object_or_404(model, pk=pk, owner=request.user)
    if request.method == "POST":
        obj.delete()
        clear_stats_cache()
        messages.success(request, "Объект удалён.")
        return redirect(success_url)

    return render(request, "mailing/confirm_delete.html", {"object": obj})


@login_required
def recipient_list(request):
    return render(
        request,
        "mailing/object_list.html",
        {
            "title": "Получатели",
            "objects": visible_objects(Recipient, request.user),
            "create_url": "mailing:recipient_create",
            "update_url": "mailing:recipient_update",
            "delete_url": "mailing:recipient_delete",
        },
    )


@login_required
def recipient_create(request):
    return edit_object(
        request,
        model=Recipient,
        form_class=RecipientForm,
        success_url="mailing:recipient_list",
        title="Добавить получателя",
    )


@login_required
def recipient_update(request, pk):
    return edit_object(
        request,
        model=Recipient,
        form_class=RecipientForm,
        success_url="mailing:recipient_list",
        title="Изменить получателя",
        pk=pk,
    )


@login_required
def recipient_delete(request, pk):
    return delete_object(
        request,
        model=Recipient,
        success_url="mailing:recipient_list",
        pk=pk,
    )


@login_required
def message_list(request):
    return render(
        request,
        "mailing/object_list.html",
        {
            "title": "Сообщения",
            "objects": visible_objects(Message, request.user),
            "create_url": "mailing:message_create",
            "update_url": "mailing:message_update",
            "delete_url": "mailing:message_delete",
        },
    )


@login_required
def message_create(request):
    return edit_object(
        request,
        model=Message,
        form_class=MessageForm,
        success_url="mailing:message_list",
        title="Добавить сообщение",
    )


@login_required
def message_update(request, pk):
    return edit_object(
        request,
        model=Message,
        form_class=MessageForm,
        success_url="mailing:message_list",
        title="Изменить сообщение",
        pk=pk,
    )


@login_required
def message_delete(request, pk):
    return delete_object(
        request,
        model=Message,
        success_url="mailing:message_list",
        pk=pk,
    )


@login_required
def mailing_list(request):
    return render(
        request,
        "mailing/object_list.html",
        {
            "title": "Рассылки",
            "objects": visible_objects(Mailing, request.user),
            "create_url": "mailing:mailing_create",
            "detail_url": "mailing:mailing_detail",
            "update_url": "mailing:mailing_update",
            "delete_url": "mailing:mailing_delete",
        },
    )


@login_required
def mailing_detail(request, pk):
    mailing = get_object_or_404(visible_objects(Mailing, request.user), pk=pk)
    mailing.update_status()
    return render(request, "mailing/mailing_detail.html", {"mailing": mailing})


@login_required
def mailing_create(request):
    return edit_object(
        request,
        model=Mailing,
        form_class=MailingForm,
        success_url="mailing:mailing_list",
        title="Создать рассылку",
    )


@login_required
def mailing_update(request, pk):
    return edit_object(
        request,
        model=Mailing,
        form_class=MailingForm,
        success_url="mailing:mailing_list",
        title="Изменить рассылку",
        pk=pk,
    )


@login_required
def mailing_delete(request, pk):
    return delete_object(
        request,
        model=Mailing,
        success_url="mailing:mailing_list",
        pk=pk,
    )


@login_required
@require_POST
def mailing_send(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)
    try:
        success_count, fail_count = send_mailing(mailing)
    except ValidationError as error:
        messages.error(request, error.message)
    else:
        messages.success(
            request,
            f"Отправлено: {success_count}, ошибок: {fail_count}",
        )
        clear_stats_cache()

    return redirect("mailing:mailing_detail", pk=pk)