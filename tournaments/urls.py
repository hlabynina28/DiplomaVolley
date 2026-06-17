from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('<int:pk>/apply/', views.tournament_apply, name='tournament_apply'),
    path('<int:pk>/withdraw/', views.tournament_withdraw, name='tournament_withdraw'),
    path('past/', views.past_tournaments, name='past_tournaments'),
    path('past/<int:pk>/', views.past_tournament_detail, name='past_tournament_detail'),

]
