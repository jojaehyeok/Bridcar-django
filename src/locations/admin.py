from django import forms
from django.contrib import admin
from django.db.models import Case, When, Value, Count, IntegerField

from locations.models import CommonLocation

from pcar.admin import DaumPostcodeSearchField


class CommonLocationAdminForm(forms.ModelForm):
    road_address = DaumPostcodeSearchField(
        label='도로명 주소',
    )


@admin.register(CommonLocation)
class CommonLocationAdmin(admin.ModelAdmin):
    form = CommonLocationAdminForm

    fields = ( 'road_address', 'detail_address', 'contact', )

    list_display = ( '__str__', 'is_favorited_by_dealer', )

    def is_favorited_by_dealer(self, obj):
        return obj.is_favorited_by_dealer == 1

    is_favorited_by_dealer.short_description = '딜러가 즐겨찾기 여부'
    is_favorited_by_dealer.admin_order_field = 'is_favorited_by_dealer'
    is_favorited_by_dealer.boolean = True

    def get_queryset(self, request):
        queryset = super(CommonLocationAdmin, self).get_queryset(request)
        queryset = queryset \
            .annotate(
                favorite_count=Count('dealer_profiles'),
                is_favorited_by_dealer=Case(
                    When(favorite_count__gt=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )

        return queryset
