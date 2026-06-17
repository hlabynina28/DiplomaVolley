import datetime
import json

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings

from .models import TrainingBooking, Court, RecurringBlock, get_time_slots, SLOT_MINUTES
from .forms import TrainingBookingForm, CancelBookingForm


def _build_grid(date):
    """
    Строит данные сетки для одной даты.
    Возвращает:
      courts     — список объектов Court
      slots      — список time-объектов (06:00, 06:30, ...)
      grid       — {court_id: {slot_time: {'count': N, 'blocked': bool, 'block_label': str}}}
    """
    courts = Court.objects.filter(is_active=True).order_by('number')
    slots = get_time_slots()
    weekday = date.weekday()

    # Все постоянные блокировки для этого дня недели
    recurring = RecurringBlock.objects.filter(
        court__in=courts, weekday=weekday, is_active=True
    ).select_related('court')

    # Все бронирования на эту дату
    bookings = TrainingBooking.objects.filter(
        date=date, court__in=courts
    ).select_related('court')

    # Инициализируем сетку
    grid = {}
    for court in courts:
        grid[court.id] = {}
        for slot in slots:
            grid[court.id][slot] = {'count': 0, 'blocked': False, 'block_label': ''}

    # Помечаем заблокированные слоты
    for block in recurring:
        for slot in slots:
            if block.covers_slot(slot):
                cell = grid[block.court_id][slot]
                cell['blocked'] = True
                cell['block_label'] = block.label or 'Тренировка секции'

    # Считаем количество записей в каждом слоте
    for booking in bookings:
        for slot in slots:
            slot_end = (
                datetime.datetime.combine(datetime.date.today(), slot)
                + datetime.timedelta(minutes=SLOT_MINUTES)
            ).time()
            # Бронирование попадает в слот если перекрывается с ним
            if booking.start_slot < slot_end and booking.end_slot > slot:
                grid[booking.court_id][slot]['count'] += 1

    return courts, slots, grid


def training_calendar(request):
    """Главная страница тренировок — выбор даты."""
    today = timezone.now().date()
    dates = [today + datetime.timedelta(days=i) for i in range(4)]
    cancel_form = CancelBookingForm()
    return render(request, 'training/calendar.html', {
        'dates': dates,
        'today': today,
        'cancel_form': cancel_form,
    })


def training_grid(request):
    """
    Сетка площадка × время для выбранной даты.
    Вызывается через AJAX (fetch) когда пользователь кликает на дату.
    Возвращает JSON для рендера сетки на клиенте.
    """
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Не указана дата'}, status=400)
    try:
        date = datetime.date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты'}, status=400)

    today = timezone.now().date()
    if date < today or date > today + datetime.timedelta(days=14):
        return JsonResponse({'error': 'Дата вне допустимого диапазона'}, status=400)

    courts, slots, grid = _build_grid(date)

    # Сериализуем для JSON
    courts_data = [{'id': c.id, 'name': str(c)} for c in courts]
    slots_data = [s.strftime('%H:%M') for s in slots]
    grid_data = {}
    for court_id, court_slots in grid.items():
        grid_data[court_id] = {}
        for slot_time, cell in court_slots.items():
            grid_data[court_id][slot_time.strftime('%H:%M')] = cell

    return JsonResponse({
        'date': date_str,
        'courts': courts_data,
        'slots': slots_data,
        'grid': grid_data,
    })


def training_book(request):
    """Создать запись на тренировку."""
    if request.method == 'POST':
        form = TrainingBookingForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                court = Court.objects.get(pk=d['court_id'])
            except Court.DoesNotExist:
                messages.error(request, 'Площадка не найдена.')
                return redirect('training_calendar')

            booking = TrainingBooking(
                court=court,
                date=d['date'],
                start_slot=d['start_time'],
                end_slot=d['end_time'],
                full_name=d['full_name'],
                phone=d['phone'],
                email=d['email'],
            )
            try:
                booking.save()  # вызывает full_clean() → проверит блокировки
                _send_booking_confirmation(booking)
                messages.success(
                    request,
                    f'Запись создана! Подтверждение отправлено на {booking.email}.'
                )
            except Exception as e:
                messages.error(request, str(e))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    label = form.fields[field].label if field in form.fields else ''
                    messages.error(request, f'{label}: {error}' if label else error)

    return redirect('training_calendar')


def training_cancel(request):
    """Отменить запись на тренировку."""
    if request.method == 'POST':
        form = CancelBookingForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            bookings = TrainingBooking.objects.filter(
                full_name__iexact=d['full_name'].strip(),
                phone=d['phone'].strip(),
                date=d['date'],
            )
            if not bookings.exists():
                messages.error(request, 'Запись не найдена. Проверьте ФИО, телефон и дату.')
            else:
                email = bookings.first().email
                count = bookings.count()
                bookings.delete()
                _send_cancellation_confirmation(email, d['full_name'], d['date'])
                label = 'Запись удалена.' if count == 1 else f'Удалено записей: {count}.'
                messages.success(request, label)
    return redirect('training_calendar')


def _send_booking_confirmation(booking):
    subject = f'Подтверждение записи на тренировку — {booking.date}'
    message = (
        f'Здравствуйте, {booking.full_name}!\n\n'
        f'Ваша запись подтверждена:\n'
        f'  Дата: {booking.date:%d.%m.%Y}\n'
        f'  Время: {booking.start_slot:%H:%M} – {booking.end_slot:%H:%M}\n'
        f'  Площадка: {booking.court}\n\n'
        f'Чтобы отменить запись, укажите на сайте:\n'
        f'  ФИО: {booking.full_name}\n'
        f'  Телефон: {booking.phone}\n'
        f'  Дата: {booking.date:%d.%m.%Y}\n\n'
    )
    send_mail(subject, message, settings.EMAIL_HOST_USER, [booking.email], fail_silently=True)


def _send_cancellation_confirmation(email, full_name, date):
    subject = f'Запись на тренировку {date} отменена'
    message = (
        f'Здравствуйте, {full_name}!\n\n'
        f'Ваша запись на {date:%d.%m.%Y} успешно отменена.\n\n'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
