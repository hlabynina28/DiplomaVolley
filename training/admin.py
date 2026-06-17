from django.contrib import admin
from .models import Court, RecurringBlock, TrainingBooking, VenueInfo


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ['number', 'name', 'is_active']
    list_editable = ['is_active']


@admin.register(RecurringBlock)
class RecurringBlockAdmin(admin.ModelAdmin):
    list_display = ['court', 'weekday', 'start_time', 'end_time', 'label', 'is_active']
    list_filter = ['court', 'weekday', 'is_active']
    list_editable = ['is_active']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['start_time'].widget.attrs['placeholder'] = '06:00'
        form.base_fields['end_time'].widget.attrs['placeholder'] = '07:00'
        return form


@admin.register(TrainingBooking)
class TrainingBookingAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'court', 'date', 'start_slot', 'end_slot']
    list_filter = ['court', 'date']
    search_fields = ['full_name', 'phone', 'email']
    date_hierarchy = 'date'


@admin.register(VenueInfo)
class VenueInfoAdmin(admin.ModelAdmin):
    list_display = ['title', 'description']

