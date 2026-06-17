from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class Tournament(models.Model):
    title = models.CharField('Название', max_length=200)
    date = models.DateField('Дата проведения')
    description = models.TextField('Описание')
    max_teams = models.PositiveIntegerField('Максимум команд', default=16)
    regulation_file = models.FileField(
        'Положение турнира',
        upload_to='regulations/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Турнир'
        verbose_name_plural = 'Турниры'
        ordering = ['date']

    def __str__(self):
        return f'{self.title} ({self.date})'

    @property
    def is_upcoming(self):
        return self.date >= timezone.now().date()

    @property
    def approved_applications(self):
        return self.applications.filter(status='approved')

    @property
    def pending_applications(self):
        return self.applications.filter(status='pending')


place_validator = RegexValidator(
    regex=r'^\d{1,3}(-\d{1,3})?$',
    message='Введите число или диапазон через тире, например: 1, 9, 11-12'
)


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]

    place = models.CharField(
        'Место', max_length=10, blank=True, default='',
        validators=[place_validator],
        help_text='Число или диапазон через тире, например: 1, 1-2, 9, 11-12'
    )
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Турнир',
    )
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField('Дата подачи', auto_now_add=True)

    player1_name = models.CharField('ФИО (1)', max_length=200)
    player1_dob = models.DateField('Дата рождения (1)')
    player1_phone = models.CharField('Номер телефона (1)', max_length=20)
    player1_city = models.CharField('Город (1)', max_length=100)

    player2_name = models.CharField('ФИО (2)', max_length=200)
    player2_dob = models.DateField('Дата рождения (2)')
    player2_phone = models.CharField('Номер телефона (2)', max_length=20)
    player2_city = models.CharField('Город (2)', max_length=100)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tournament', 'player1_phone', 'player2_phone'],
                name='unique_application_per_tournament'
            )
        ]

    def __str__(self):
        return f'{self.player1_name} & {self.player2_name} → {self.tournament}'


class TournamentResult(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name='Турнир',
    )
    place = models.PositiveIntegerField('Место')
    players = models.ForeignKey(
        to='Application',
        on_delete=models.CASCADE,
        related_name='players',
        verbose_name='Игроки',
        null=True,
        blank=True,
    )
    score = models.CharField('Счёт / результат', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
        ordering = ['place']

    def __str__(self):
        return f'{self.place}. {self.team_name} — {self.tournament}'
