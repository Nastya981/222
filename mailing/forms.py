from django import forms
from .models import Recipient, Message, Mailing


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ('email', 'full_name', 'comment')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('subject', 'body')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ('start_time', 'end_time', 'message', 'recipients')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        # Для поля с множественным выбором
        self.fields['recipients'].widget.attrs.update({'class': 'form-control', 'size': 10})