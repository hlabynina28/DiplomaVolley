from django import forms
from django.utils import timezone
import datetime
from .models import TrainingBooking, get_time_slots, SLOT_MINUTES


def _time_choices():
    """Возвращает choices для select: [('06:00', '06:00'), ...]"""
    return [(t.strftime('%H:%M'), t.strftime('%H:%M')) for t in get_time_slots()]


class TrainingBookingForm(forms.Form):
    """
    Форма записи на тренировку.
    Дата и площадка передаются скрытыми полями (выбраны в сетке),
    время — двумя select-ами.
    """
    court_id = forms.IntegerField(widget=forms.HiddenInput())
    date = forms.DateField(widget=forms.HiddenInput())

    start_slot = forms.ChoiceField(
        label='Начало',
        choices=[],  # заполним в __init__
    )
    end_slot = forms.ChoiceField(
        label='Конец',
        choices=[],
    )

    full_name = forms.CharField(label='ФИО', max_length=200)
    phone = forms.CharField(
        label='Телефон', max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'})
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'example@mail.ru'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = _time_choices()
        self.fields['start_slot'].choices = choices
        # Для конца — добавляем последний слот + 30 мин (22:00)
        end_choices = choices[1:] + [('22:00', '22:00')]
        self.fields['end_slot'].choices = end_choices

    def clean(self):
        cleaned_data = super().clean()
        start_str = cleaned_data.get('start_slot')
        end_str = cleaned_data.get('end_slot')
        date = cleaned_data.get('date')

        if start_str and end_str:
            start = datetime.datetime.strptime(start_str, '%H:%M').time()
            end = datetime.datetime.strptime(end_str, '%H:%M').time()
            if end <= start:
                raise forms.ValidationError('Время конца должно быть позже начала.')
            cleaned_data['start_time'] = start
            cleaned_data['end_time'] = end

        if date:
            today = timezone.now().date()
            two_weeks = today + datetime.timedelta(days=14)
            if date < today:
                raise forms.ValidationError('Нельзя записаться на прошедшую дату.')
            if date > two_weeks:
                raise forms.ValidationError('Запись доступна только на ближайшие две недели.')

        return cleaned_data


class CancelBookingForm(forms.Form):
    full_name = forms.CharField(label='ФИО', max_length=200)
    phone = forms.CharField(label='Телефон', max_length=20)
    date = forms.DateField(
        label='Дата записи',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
