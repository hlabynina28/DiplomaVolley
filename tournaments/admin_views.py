from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Tournament, Application
from .forms import TournamentForm


@login_required
def admin_applications_list(request):
    tournaments = Tournament.objects.filter(date__gte=timezone.now().date()).prefetch_related('applications')
    data = []
    for t in tournaments:
        data.append({
            'tournament': t,
            'pending_count': t.pending_applications.count(),
            'approved_count': t.approved_applications.count(),
        })
    return render(request, 'admin_panel/applications_list.html', {'data': data})


@login_required
def admin_tournament_applications(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    pending = tournament.pending_applications.all()
    approved = tournament.approved_applications.all()
    return render(request, 'admin_panel/tournament_applications.html', {
        'tournament': tournament,
        'pending': pending,
        'approved': approved,
    })


@login_required
def admin_approve_application(request, pk, app_id):
    application = get_object_or_404(Application, pk=app_id, tournament_id=pk)
    if request.method == 'POST':
        application.status = 'approved'
        application.save()
        messages.success(request, f'Заявка {application.player1_name} & {application.player2_name} одобрена.')
    return redirect('admin_tournament_applications', pk=pk)


@login_required
def admin_reject_application(request, pk, app_id):
    application = get_object_or_404(Application, pk=app_id, tournament_id=pk)
    if request.method == 'POST':
        name = f'{application.player1_name} & {application.player2_name}'
        application.status = 'rejected'
        application.save()
        # application.delete()
        # messages.success(request, f'Заявка {name} удалена.')
    return redirect('admin_tournament_applications', pk=pk)


@login_required
def admin_tournament_create(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save()
            messages.success(request, f'Турнир «{tournament.title}» создан.')
            return redirect('admin_tournament_applications', pk=tournament.pk)
    else:
        form = TournamentForm()
    return render(request, 'admin_panel/tournament_form.html', {
        'form': form,
        'action': 'Создать турнир',
    })


@login_required
def admin_tournament_edit(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Турнир обновлён.')
            return redirect('admin_tournament_applications', pk=pk)
    else:
        form = TournamentForm(instance=tournament)
    return render(request, 'admin_panel/tournament_form.html', {
        'form': form,
        'action': 'Редактировать турнир',
        'tournament': tournament,
    })


@login_required
def admin_tournament_delete(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.method == 'POST':
        name = tournament.title
        tournament.delete()
        messages.success(request, f'Турнир «{name}» удалён.')
        return redirect('admin_applications_list')
    return render(request, 'admin_panel/tournament_confirm_delete.html', {
        'tournament': tournament,
    })



from .forms import ResultsForm

@login_required
def admin_tournament_results(request, pk):
    """Страница проставления мест для одобренных пар турнира."""
    tournament = get_object_or_404(Tournament, pk=pk)
    approved = tournament.applications.filter(status='approved').order_by(
        'player1_name'
    )

    if request.method == 'POST':
        form = ResultsForm(request.POST, applications=approved)
        if form.is_valid():
            for app in approved:
                place = form.cleaned_data.get(f'place_{app.pk}', '').strip()
                if app.place != place:
                    app.place = place
                    app.save(update_fields=['place'])
            messages.success(request, 'Результаты сохранены.')
            return redirect('admin_tournament_applications', pk=pk)
    else:
        form = ResultsForm(applications=approved)

    # Объединяем поля формы с данными заявок для удобного рендера в шаблоне
    rows = []
    for app in approved:
        rows.append({
            'app': app,
            'field': form[f'place_{app.pk}'],
        })

    return render(request, 'admin_panel/tournament_results.html', {
        'tournament': tournament,
        'form': form,
        'rows': rows,
    })