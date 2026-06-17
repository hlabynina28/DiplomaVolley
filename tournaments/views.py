from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError

from training.models import VenueInfo
from .models import Tournament, Application
from .forms import ApplicationForm, WithdrawApplicationForm


def home(request):
    """Главная страница — предстоящие турниры."""
    upcoming = Tournament.objects.filter(date__gte=timezone.now().date())
    past = Tournament.objects.filter(date__lt=timezone.now().date())
    return render(request, 'tournaments/home.html', {
        'upcoming': upcoming,
        'past': past,
    })


def venue(request):
    """Страница информации о площадке."""
    return render(request, 'tournaments/venue.html', context={
        'venue': VenueInfo.objects.first(),
    })


def tournament_detail(request, pk):
    """Страница турнира."""
    tournament = get_object_or_404(Tournament, pk=pk)
    apply_form = ApplicationForm()
    withdraw_form = WithdrawApplicationForm()
    return render(request, 'tournaments/tournament_detail.html', {
        'tournament': tournament,
        'apply_form': apply_form,
        'withdraw_form': withdraw_form,
    })


def tournament_apply(request, pk):
    """Подать заявку на турнир."""
    tournament = get_object_or_404(Tournament, pk=pk)

    if not tournament.is_upcoming:
        messages.error(request, 'Этот турнир уже завершён.')
        return redirect('tournament_detail', pk=pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            try:
                application = form.save(commit=False)
                application.tournament = tournament
                application.save()
                messages.success(request, 'Ваша заявка успешно подана! Ожидайте подтверждения.')
            except IntegrityError:
                messages.error(request, 'Заявка с такими данными уже существует.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}' if field != '__all__' else error)
    return redirect('tournament_detail', pk=pk)


def tournament_withdraw(request, pk):
    """Удалить заявку на турнир."""
    tournament = get_object_or_404(Tournament, pk=pk)

    if request.method == 'POST':
        form = WithdrawApplicationForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                application = Application.objects.get(
                    tournament=tournament,
                    player1_name__iexact=d['player1_name'].strip(),
                    player1_phone=d['player1_phone'].strip(),
                    player2_name__iexact=d['player2_name'].strip(),
                    player2_phone=d['player2_phone'].strip(),
                )
                application.delete()
                messages.success(request, 'Заявка успешно удалена.')
            except Application.DoesNotExist:
                messages.error(request, 'Заявка не найдена. Проверьте введённые данные.')
    return redirect('tournament_detail', pk=pk)


def past_tournaments(request):
    """Список завершённых турниров."""
    past = Tournament.objects.filter(
        date__lt=timezone.now().date()
    ).prefetch_related('results')
    return render(request, 'tournaments/past_tournaments.html', {'past': past})


def past_tournament_detail(request, pk):
    """Страница завершённого турнира с участниками и местами."""
    tournament = get_object_or_404(Tournament, pk=pk)
    approved = tournament.applications.filter(status='approved')
    results = tournament.results.all()  # уже отсортированы по place

    # Строим словарь {team_name: place} для удобства в шаблоне
    result_map = {r.team_name.strip().lower(): r for r in results}

    return render(request, 'tournaments/past_tournament_detail.html', {
        'tournament': tournament,
        'approved': approved,
        'results': results,
        'result_map': result_map,
    })