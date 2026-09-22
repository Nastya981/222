from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Recipient, Message, Mailing, Attempt
from .forms import RecipientForm, MessageForm, MailingForm


def home(request):
    """Главная страница со статистикой"""
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now(),
        status='Запущена'
    ).count()
    unique_recipients = Recipient.objects.count()

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
    }
    return render(request, 'mailing/home.html', context)


# === Получатели ===

def recipient_list(request):
    recipients = Recipient.objects.all()
    return render(request, 'mailing/recipient_list.html', {'recipients': recipients})


def recipient_create(request):
    if request.method == 'POST':
        form = RecipientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Получатель добавлен')
            return redirect('mailing:recipient_list')
    else:
        form = RecipientForm()
    return render(request, 'mailing/recipient_form.html', {'form': form, 'title': 'Добавить получателя'})


def recipient_update(request, pk):
    recipient = get_object_or_404(Recipient, pk=pk)
    if request.method == 'POST':
        form = RecipientForm(request.POST, instance=recipient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Получатель обновлён')
            return redirect('mailing:recipient_list')
    else:
        form = RecipientForm(instance=recipient)
    return render(request, 'mailing/recipient_form.html', {'form': form, 'title': 'Редактировать получателя'})


def recipient_delete(request, pk):
    recipient = get_object_or_404(Recipient, pk=pk)
    if request.method == 'POST':
        recipient.delete()
        messages.success(request, 'Получатель удалён')
        return redirect('mailing:recipient_list')
    return render(request, 'mailing/recipient_confirm_delete.html', {'recipient': recipient})


# === Сообщения ===

def message_list(request):
    messages_list = Message.objects.all()
    return render(request, 'mailing/message_list.html', {'messages': messages_list})


def message_create(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сообщение добавлено')
            return redirect('mailing:message_list')
    else:
        form = MessageForm()
    return render(request, 'mailing/message_form.html', {'form': form, 'title': 'Добавить сообщение'})


def message_update(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сообщение обновлено')
            return redirect('mailing:message_list')
    else:
        form = MessageForm(instance=message)
    return render(request, 'mailing/message_form.html', {'form': form, 'title': 'Редактировать сообщение'})


def message_delete(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        message.delete()
        messages.success(request, 'Сообщение удалено')
        return redirect('mailing:message_list')
    return render(request, 'mailing/message_confirm_delete.html', {'message': message})


# === Рассылки ===

def mailing_list(request):
    mailings = Mailing.objects.all()
    return render(request, 'mailing/mailing_list.html', {'mailings': mailings})


def mailing_detail(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.update_status()
    return render(request, 'mailing/mailing_detail.html', {'mailing': mailing})


def mailing_create(request):
    if request.method == 'POST':
        form = MailingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рассылка создана')
            return redirect('mailing:mailing_list')
    else:
        form = MailingForm()
    return render(request, 'mailing/mailing_form.html', {'form': form, 'title': 'Создать рассылку'})


def mailing_update(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if request.method == 'POST':
        form = MailingForm(request.POST, instance=mailing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рассылка обновлена')
            return redirect('mailing:mailing_list')
    else:
        form = MailingForm(instance=mailing)
    return render(request, 'mailing/mailing_form.html', {'form': form, 'title': 'Редактировать рассылку'})


def mailing_delete(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if request.method == 'POST':
        mailing.delete()
        messages.success(request, 'Рассылка удалена')
        return redirect('mailing:mailing_list')
    return render(request, 'mailing/mailing_confirm_delete.html', {'mailing': mailing})


def mailing_send(request, pk):
    """Отправка рассылки по требованию"""
    mailing = get_object_or_404(Mailing, pk=pk)
    now = timezone.now()

    if not (mailing.start_time <= now <= mailing.end_time):
        messages.error(request, 'Отправка невозможна: текущее время вне диапазона рассылки')
        return redirect('mailing:mailing_detail', pk=pk)

    recipients = mailing.recipients.all()
    if not recipients:
        messages.warning(request, 'У рассылки нет получателей')
        return redirect('mailing:mailing_detail', pk=pk)

    success_count = 0
    fail_count = 0

    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            Attempt.objects.create(
                status='Успешно',
                server_response='OK',
                mailing=mailing
            )
            success_count += 1
        except Exception as e:
            Attempt.objects.create(
                status='Не успешно',
                server_response=str(e),
                mailing=mailing
            )
            fail_count += 1

    messages.success(request, f'Отправлено: {success_count}, ошибок: {fail_count}')
    return redirect('mailing:mailing_detail', pk=pk)