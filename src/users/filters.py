from django.db.models import Q
from django.contrib.admin import SimpleListFilter

from pcar.admin import InputFilter


class DealerCompanyNameInputFilter(InputFilter):
    parameter_name = 'dealer__dealer_profile__company__name'
    title = '업체명'

    def queryset(self, request, queryset):
        if self.value() is not None:
            client_company_name = self.value()

            return queryset.filter(
                Q(dealer_profile__company__name=client_company_name)
            )
