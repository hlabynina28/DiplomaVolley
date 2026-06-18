from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from tournaments.views import home, venue

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', home, name='home'),
    path('venue/', venue, name='venue'),
    path('tournament/', include('tournaments.urls')),
    path('training/', include('training.urls')),
    path('admin-panel/login/',
         auth_views.LoginView.as_view(template_name='admin_panel/login.html'),
         name='login'),
    path('admin-panel/logout/',
         auth_views.LogoutView.as_view(next_page='/'),
         name='logout'),
    path('admin-panel/', include('tournaments.admin_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]