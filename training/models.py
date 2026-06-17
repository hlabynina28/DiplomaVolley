from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from djrichtextfield.models import RichTextField

# # Количество площадок — единственное место, которое нужно менять при добавлении площадки
# COURT_COUNT = 4
#
# COURT_CHOICES = [(i, f'Площадка {i}') for i in range(1, COURT_COUNT + 1)]

SCHEDULE_START = datetime.time(6, 0)
SCHEDULE_END = datetime.time(22, 0)
SLOT_MINUTES = 30


def get_time_slots():
    """Возвращает список всех временных слотов [(time, 'HH:MM'), ...]."""
    slots = []
    current = datetime.datetime.combine(datetime.date.today(), SCHEDULE_START)
    end = datetime.datetime.combine(datetime.date.today(), SCHEDULE_END)
    while current < end:
        slots.append(current.time())
        current += datetime.timedelta(minutes=SLOT_MINUTES)
    return slots


class Court(models.Model):
    """
    Площадка.
    Создаётся через django-admin, количество не захардкожено."""
    number = models.PositiveSmallIntegerField('Номер площадки', unique=True)
    name = models.CharField('Название', max_length=100, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Площадка'
        verbose_name_plural = 'Площадки'
        ordering = ['number']

    def __str__(self):
        return self.name or f'Площадка {self.number}'


class RecurringBlock(models.Model):
    """
    Тренировки постоянные
    Например: каждый вторник и четверг 06:00–07:00, площадка 2.
    Администратор создаёт в django-admin.
    """
    WEEKDAY_CHOICES = [
        (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
        (3, 'Четверг'), (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье'),
    ]

    court = models.ForeignKey(Court, on_delete=models.CASCADE,
                              related_name='recurring_blocks', verbose_name='Площадка')
    weekday = models.PositiveSmallIntegerField('День недели', choices=WEEKDAY_CHOICES)
    start_time = models.TimeField('Начало')
    end_time = models.TimeField('Конец')
    label = models.CharField('Подпись (что за тренировка)', max_length=100, blank=True)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Постоянная тренировка'
        verbose_name_plural = 'Постоянные тренировки'

    def __str__(self):
        day = dict(self.WEEKDAY_CHOICES)[self.weekday]
        return f'{self.court} — {day} {self.start_time:%H:%M}–{self.end_time:%H:%M} ({self.label})'

    def covers_slot(self, slot_time):
        """Проверяет, попадает ли слот (начало получаса) в эту блокировку."""
        slot_end = (datetime.datetime.combine(datetime.date.today(), slot_time)
                    + datetime.timedelta(minutes=SLOT_MINUTES)).time()
        return self.start_time < slot_end and self.end_time > slot_time


class TrainingBooking(models.Model):
    """
    Запись на тренировку.
    Один объект = одна или несколько смежных ячеек
    (пользователь выбирает дату, площадку, start_slot и end_slot).
    """
    court = models.ForeignKey(Court, on_delete=models.CASCADE,
                              related_name='bookings', verbose_name='Площадка')
    date = models.DateField('Дата')
    # start_slot и end_slot — границы бронирования (end_slot не включён)
    start_slot = models.TimeField('Начало (слот)')
    end_slot = models.TimeField('Конец (слот)')   # например 10:30 значит "до 10:30"

    full_name = models.CharField('ФИО', max_length=200)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Запись на тренировку'
        verbose_name_plural = 'Записи на тренировки'
        ordering = ['date', 'start_slot']

    def __str__(self):
        return (f'{self.full_name} — {self.court} '
                f'{self.date} {self.start_slot:%H:%M}–{self.end_slot:%H:%M}')

    def clean(self):
        if not (self.start_slot and self.end_slot and self.date and self.court_id):
            return

        today = timezone.now().date()
        two_weeks = today + datetime.timedelta(days=14)

        if self.date < today:
            raise ValidationError('Нельзя записаться на прошедшую дату.')
        if self.date > two_weeks:
            raise ValidationError('Запись доступна только на ближайшие две недели.')
        if self.end_slot <= self.start_slot:
            raise ValidationError('Конец должен быть позже начала.')

        # Проверяем, не заблокирован ли хотя бы один слот постоянной тренировкой
        weekday = self.date.weekday()
        blocks = RecurringBlock.objects.filter(
            court=self.court_id, weekday=weekday, is_active=True
        )
        slots = get_time_slots()
        my_slots = [s for s in slots if self.start_slot <= s < self.end_slot]
        for block in blocks:
            for s in my_slots:
                if block.covers_slot(s):
                    raise ValidationError(
                        f'Слот {s:%H:%M} заблокирован постоянной тренировкой: {block.label or str(block)}.'
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class VenueInfo(models.Model):
    title = models.CharField(verbose_name='Название площадки', max_length=100)
    description = models.TextField(default='Информация о площадке', blank=True)

    class Meta:
        verbose_name = 'Информация'
        verbose_name_plural = 'Информации'


