from django import forms
from .models import Application, Tournament, place_validator


class ApplicationForm(forms.ModelForm):
    player1_dob = forms.DateField(
        label='Дата рождения (1)',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    player2_dob = forms.DateField(
        label='Дата рождения (2)',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = Application
        fields = [
            'player1_name', 'player1_dob', 'player1_phone', 'player1_city',
            'player2_name', 'player2_dob', 'player2_phone', 'player2_city',
        ]
        widgets = {
            'player1_phone': forms.TextInput(),
            'player2_phone': forms.TextInput(),
            'player1_city': forms.TextInput(),
            'player2_city': forms.TextInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1_name = cleaned_data.get('player1_name', '').strip().lower()
        p2_name = cleaned_data.get('player2_name', '').strip().lower()
        if p1_name and p2_name and p1_name == p2_name:
            raise forms.ValidationError('Участники не могут быть одним и тем же человеком.')
        return cleaned_data


class WithdrawApplicationForm(forms.Form):
    player1_name = forms.CharField(label='ФИО (1)', max_length=200)
    player1_phone = forms.CharField(label='Номер телефона (1)', max_length=20)
    player2_name = forms.CharField(label='ФИО (2)', max_length=200)
    player2_phone = forms.CharField(label='Номер телефона (2)', max_length=20)


class TournamentForm(forms.ModelForm):

    class Meta:
        model = Tournament
        fields = ['title', 'date', 'description', 'max_teams', 'regulation_file']
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'max_teams': 'Максимум команд',
            'regulation_file': 'Положение турнира',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }



class ResultsForm(forms.Form):
    """
    Динамическая форма: одно поле place_<id> для каждой одобренной заявки.
    Создаётся в view с передачей queryset заявок.
    """
    def __init__(self, *args, applications=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.applications = applications or []
        for app in self.applications:
            self.fields[f'place_{app.pk}'] = forms.CharField(
                label='', required=False, max_length=10,
                initial=app.place,
                validators=[place_validator],
                widget=forms.TextInput(attrs={
                    'class': 'form-control form-control-sm',
                    'style': 'width:90px;',
                    'placeholder': '—',
                }),
            )