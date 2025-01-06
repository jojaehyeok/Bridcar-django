from django import forms
from django.forms import widgets
from django.contrib import admin
from django.contrib.gis.geos import Point

class LatLongWidget(forms.MultiWidget):
    def __init__(self, attrs=None, date_format=None, time_format=None):
        widgets = (forms.TextInput(attrs=attrs),
                   forms.TextInput(attrs=attrs))

        super(LatLongWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return tuple(value.coords)

        return (None, None)

    def value_from_datadict(self, data, files, name):
        mylat = data[name + '_0']
        mylong = data[name + '_1']

        try:
            point = Point(float(mylat), float(mylong))
        except ValueError:
            return ''

        return point


class InputFilter(admin.SimpleListFilter):
    template = 'pcar/admin/input_filter.html'

    def lookups(self, request, model_admin):
        return ((),)

    def choices(self, changelist):
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )

        yield all_choice


class DaumPostcodeSearchWidget(widgets.TextInput):
    template_name = 'pcar/widget/daum_postcode_search.html'


class DaumPostcodeSearchField(forms.CharField):
    widget = DaumPostcodeSearchWidget
