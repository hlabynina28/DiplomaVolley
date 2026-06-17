from django.urls import path
from .admin_views import (
    admin_applications_list,
    admin_tournament_applications,
    admin_approve_application,
    admin_reject_application,
    admin_tournament_create,
    admin_tournament_edit,
    admin_tournament_delete, admin_tournament_results,
)

urlpatterns = [
    path('applications/', admin_applications_list, name='admin_applications_list'),
    path('applications/<int:pk>/', admin_tournament_applications, name='admin_tournament_applications'),
    path('applications/<int:pk>/approve/<int:app_id>/', admin_approve_application, name='admin_approve_application'),
    path('applications/<int:pk>/reject/<int:app_id>/', admin_reject_application, name='admin_reject_application'),
    path('tournaments/create/', admin_tournament_create, name='admin_tournament_create'),
    path('tournaments/<int:pk>/edit/', admin_tournament_edit, name='admin_tournament_edit'),
    path('tournaments/<int:pk>/delete/', admin_tournament_delete, name='admin_tournament_delete'),
    path('applications/<int:pk>/results/', admin_tournament_results, name='admin_tournament_results'),

]
