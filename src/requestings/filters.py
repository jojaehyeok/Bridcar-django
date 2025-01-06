from django.db.models import Q
from django.contrib.admin import SimpleListFilter

from pcar.admin import InputFilter


class RequestingHistoryStatusFilter(SimpleListFilter):
    title = '의뢰 상태 필터'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return [
            ('waiting_allocations', '배차 대기중인 의뢰만'),
            ('ongoing_requestings', '진행중인 의뢰만'),
            ('cancelled_requestings', '작업이 취소된 의뢰만'),
        ]

    def queryset(self, request, queryset):
        filter_value = self.value()

        if filter_value == 'waiting_allocations':
            return queryset.distinct().filter(
                Q(status='WAITING_AGENT')| \
                Q(status='WAITING_DELIVERER')
            )
        elif filter_value == 'ongoing_requestings':
            return queryset.distinct() \
                .exclude(
                    Q(status='WAITING_AGENT')| \
                    Q(status='WAITING_DELIVERER')| \
                    Q(status='CANCELLED')
                )
        elif filter_value == 'cancelled_requestings':
            return queryset.distinct().filter(Q(status='CANCELLED'))

        return queryset.exclude(Q(status='DONE'))


class RequestingSettlementClientNameInputFilter(InputFilter):
    parameter_name = 'requesting_history__client__name'
    title = '딜러 이름'

    def queryset(self, request, queryset):
        if self.value() is not None:
            client_name = self.value()

            return queryset.filter(
                Q(requesting_history__client__name=client_name)
            )


class RequestingSettlementClientCompanyNameInputFilter(InputFilter):
    parameter_name = 'requesting_history__client__company__name'
    title = '업체명'

    def queryset(self, request, queryset):
        if self.value() is not None:
            client_company_name = self.value()

            return queryset.filter(
                Q(requesting_history__client__dealer_profile__company__name=client_company_name)
            )


class RequestingSettlementAdminProfileIdInputFilter(InputFilter):
    parameter_name = 'requesting_history__agent__agent_profile__id'
    title = '평카인 사번'

    def queryset(self, request, queryset):
        if self.value() is not None:
            agent_profile_id = self.value()

            return queryset.filter(
                Q(user__agent_profile__id=agent_profile_id)
            )
