from django.urls import path
from . import views

urlpatterns = [
    path('', views.training_calendar, name='training_calendar'),
    path('grid/', views.training_grid, name='training_grid'),   # AJAX endpoint
    path('book/', views.training_book, name='training_book'),
    path('cancel/', views.training_cancel, name='training_cancel'),
]
