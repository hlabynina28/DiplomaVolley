# Beach Volleyball Court — Django App

## Быстрый старт

```bash
# 1. Установить зависимости
pip install django

# 2. Применить миграции
python manage.py makemigrations tournaments training
python manage.py migrate

# 3. Создать суперпользователя (для входа в /admin-panel/)
python manage.py createsuperuser

# 4. Запустить сервер
python manage.py runserver
```

## Страницы

| URL | Описание |
|-----|----------|
| `/` | Главная — список предстоящих турниров |
| `/tournament/<id>/` | Страница турнира (заявки / результаты) |
| `/tournament/<id>/apply/` | POST: подать заявку |
| `/tournament/<id>/withdraw/` | POST: удалить заявку |
| `/training/` | Календарь тренировок |
| `/training/book/` | POST: записаться |
| `/training/cancel/` | POST: отменить запись |
| `/venue/` | Информация о площадке |
| `/admin-panel/login/` | Вход для администраторов |
| `/admin-panel/applications/` | Список турниров с заявками (только авторизованным) |
| `/admin-panel/applications/<id>/` | Заявки конкретного турнира |
| `/django-admin/` | Стандартная Django-админка |

## Email

В `settings.py` по умолчанию стоит `console` backend — письма печатаются в терминал.
Для продакшна замени на SMTP (раскомментируй секцию в `settings.py`).

## Структура проекта

```
beach_volleyball/
├── manage.py
├── beach_volleyball/       # Настройки проекта
│   ├── settings.py
│   └── urls.py
├── tournaments/            # Турниры и заявки
│   ├── models.py           # Tournament, Application, TournamentResult
│   ├── views.py            # Публичные view (главная, страница турнира)
│   ├── admin_views.py      # View для администраторов
│   ├── forms.py            # ApplicationForm, WithdrawApplicationForm
│   ├── urls.py             # /tournament/...
│   └── admin_urls.py       # /admin-panel/...
├── training/               # Тренировки
│   ├── models.py           # TrainingBooking
│   ├── views.py            # Календарь, запись, отмена + email
│   ├── forms.py            # TrainingBookingForm, CancelBookingForm
│   ├── urls.py             # /training/...
│   └── templatetags/
│       └── training_tags.py  # Фильтр dict_get для шаблонов
└── templates/
    ├── base.html
    ├── tournaments/
    │   ├── home.html
    │   ├── tournament_detail.html
    │   └── venue.html
    ├── training/
    │   └── calendar.html
    └── admin_panel/
        ├── login.html
        ├── applications_list.html
        └── tournament_applications.html
```

## Модели БД

### Tournament
- `title`, `date`, `description`, `max_teams`

### Application
- FK → Tournament
- `status`: pending / approved / rejected
- `player1_name`, `player1_dob`, `player1_phone`
- `player2_name`, `player2_dob`, `player2_phone`
- UniqueConstraint по (tournament, player1_phone, player2_phone)

### TournamentResult
- FK → Tournament
- `place`, `team_name`, `score`

### TrainingBooking
- `court` (1–4), `date`, `start_time`, `end_time`
- `full_name`, `phone`, `email`
- Валидация: макс 4 часа, только ближайшие 14 дней, нет пересечений по корту
