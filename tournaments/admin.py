from django.contrib import admin
from .models import Tournament, Application, TournamentResult


class ApplicationInline(admin.TabularInline):
    model = Application
    extra = 0
    readonly_fields = ['submitted_at']


class TournamentResultInline(admin.TabularInline):
    model = TournamentResult
    extra = 0


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'is_upcoming', 'max_teams']
    list_filter = ['date']
    inlines = [ApplicationInline, TournamentResultInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['player1_name', 'player2_name', 'tournament', 'status', 'submitted_at']
    list_filter = ['status', 'tournament']
    search_fields = ['player1_name', 'player2_name', 'player1_phone', 'player2_phone']
