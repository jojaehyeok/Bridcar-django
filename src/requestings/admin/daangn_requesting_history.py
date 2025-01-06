import locale
from copy import deepcopy
from urllib.parse import quote

from django import forms
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.forms import HiddenInput
from django.contrib.gis.measure import D
from django.utils.html import format_html
from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from import_export.admin import ExportActionMixin, ExportActionModelAdmin, ImportExportModelAdmin

from nested_admin import NestedModelAdmin, NestedStackedInline

from dynamic_raw_id.admin import DynamicRawIDMixin

from rangefilter.filters import DateTimeRangeFilter

from requestings.models import DaangnRequestingHistory, FinishedDaangnRequestingHistory, \
    DaangnRequestingSettlement

from requestings.filters import RequestingHistoryStatusFilter, RequestingSettlementClientNameInputFilter, \
                                RequestingSettlementClientCompanyNameInputFilter, RequestingSettlementAdminProfileIdInputFilter

from requestings.forms import RequestingHistoryAdminForm, DaangnRequestingHistoryAdminForm
from requestings.model_resources import RequestingSettlementResource
from requestings.constants import REQUESTING_TYPES, REQUESTING_STATUS

from vehicles.models import Car, CarEvaluationResult, CarEvaluationImage, CarhistoryResult, \
                            PerformanceCheckRecord, CarEvaluationSheet

from users.models import Agent, BalanceHistory

from locations.utils import get_driving_distance_with_kakao

from notifications.models import Notification

from daangn.models import DaangnRequestingInformation, DaangnRequestingRequiredDocument
from daangn.utils import DaangnRequestingWebhookSender

from pcar.admin import InputFilter

from requestings.forms import AddRequestingHistoryAdminForm
from requestings.utils import generate_requesting_settlement_xlsx

from .requesting_history import RequestingHistoryAdmin, RequestingCarInlineAdmin, RequestingAdditionalCostAdmin, \
    RequestingDeliveryResultAdmin, RequestingSettlementAdmin

from .common import requesting_history_path_getter, DisableModifyByRequestingStatusMixin


@requesting_history_path_getter('requesting_history')
class DaangnRequestingRequiredDocumentAdmin(NestedStackedInline):
    can_delete = False
    max_num = 0
    extra = 0
    model = DaangnRequestingRequiredDocument

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class DaangnRequestingInformationAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = DaangnRequestingInformation
    can_delete = False

    inlines = [
        DaangnRequestingRequiredDocumentAdmin,
    ]

    readonly_fields = [ 'is_paid', 'initial_reservation_date', ]


@admin.register(DaangnRequestingHistory)
class DaangnRequestingHistoryAdmin(RequestingHistoryAdmin):
    form = DaangnRequestingHistoryAdminForm

    list_display = [
        'id', 'car_number', 'styled_type', 'styled_status', 'daangn_confirmation_status', 'created_at', 'elapsed_time', 'reservation_date', 'source_location_address', \
        'destination_location_address', 'car_type', 'get_evaluation_cost', 'get_inspection_cost', 'get_delivering_cost', 'get_client', 'get_agent', 'get_deliverer',
    ]

    edit_fieldsets = (
        (
            '기본 내용', {
                'fields': [
                    'id', 'type', 'status', 'client', 'deliverer', 'skip_fee_for_deliverer', 'external_client_name', 'external_client_mobile_number', \
                    'reservation_date', 'estimated_service_date', 'daangn_initial_reservation_date', 'daangn_requesting_information_is_paid', \
                    'daangn_requesting_information_is_forced_exposure', 'source_location', 'destination_location', 'distance_between_source_destination', \
                    'stopovers', 'memo',
                ]
            },
        ),
        (
            '요금 내용', {
                'fields': (
                    'evaluation_cost', 'inspection_cost', 'delivering_cost', 'additional_suggested_cost', 'is_onsite_payment',
                )
            },
        ),
        (
            '기타 내용', {
                'fields': (
                    'fee_payment_histories', 'is_delivery_transferred', 'delivery_proceed_decided_at', \
                    'confirmation_inspection_result_at', 'hook_url',
                )
            }
        ),
    )

    readonly_fields = ( 'id', 'daangn_initial_reservation_date', )

    exclude = [ 'has_agent_delivery_start', ]

    list_filter = [ 'daangn_requesting_information__is_paid', RequestingHistoryStatusFilter, ]

    inlines = [
        DaangnRequestingInformationAdmin,
        RequestingCarInlineAdmin,
        RequestingAdditionalCostAdmin,
        RequestingDeliveryResultAdmin,
    ]

    def get_queryset(self, obj):
        return DaangnRequestingHistory.objects.exclude(status='DONE')

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return super(DaangnRequestingHistoryAdmin, self).get_fieldsets(request, obj)
        else:
            if obj.status == 'DELIVERING_DONE' or obj.status == 'DONE':
                new_fieldsets = deepcopy(self.edit_fieldsets)

                try:
                    new_fieldsets[0][1]['fields'].remove('daangn_requesting_information_is_paid')
                    new_fieldsets[0][1]['fields'].remove('daangn_requesting_information_is_forced_exposure')

                    return new_fieldsets
                except:
                    pass

            return self.edit_fieldsets

    def has_change_permission(self, request, obj=None):
        if obj is not None and (obj.status == 'DELIVERING_DONE' or obj.status == 'DONE'):
            return False

        return super().has_change_permission(request, obj=obj)

    def daangn_confirmation_status(self, obj):
        if obj.daangn_requesting_information.is_paid == True:
            return '확정'
        else:
            if obj.daangn_requesting_information.is_forced_exposure:
                return '미확정 (강제 노출)'
            else:
                return '미확정'

    daangn_confirmation_status.short_description = '확정여부'
    daangn_confirmation_status.admin_order_field = 'daangn_requesting_information__is_paid'

    def cancel_requesting(self, request, queryset):
        for requesting_history in queryset:
            if requesting_history.status == 'CANCELLED' or requesting_history.status == 'DONE':
                continue

            for fee_payment_history in requesting_history.fee_payment_histories.all():
                fee_payment_history.refund_fee()

            webhook_sender = DaangnRequestingWebhookSender(
                requesting_history.hook_url,
                requesting_id=requesting_history.id,
                reason='REQUESTING_CANCELLED',
            )

            webhook_sender.start()

            requesting_history.status = 'CANCELLED'
            requesting_history.save()

        messages.success(request, '의뢰가 취소되었습니다.')

    cancel_requesting.short_description = '의뢰 취소하기 (아직 시작되지 않은경우만 취소가능)'

    def daangn_initial_reservation_date(self, obj):
        return timezone.localtime(obj.daangn_requesting_information.initial_reservation_date) \
            .strftime('%Y년 %m월 %d일 %H:%M:%S %p')

    daangn_initial_reservation_date.short_description = '(당근) 최초 예약 일시'


@admin.register(FinishedDaangnRequestingHistory)
class FinishedDaangnRequestingHistoryAdmin(DaangnRequestingHistoryAdmin):
    def get_queryset(self, obj):
        return DaangnRequestingHistory.objects.filter(status='DONE')

    def has_add_permission(self, obj):
        return False


@admin.register(DaangnRequestingSettlement)
class DaangnRequestingSettlementAdmin(RequestingSettlementAdmin):
    list_display = [
        'id', 'get_requesting_history', 'requesting_type', 'requesting_history_created_at', 'requesting_end_at', 'source_location_address',
        'destination_location_address', 'car_type', 'car_number', 'get_evaluation_cost', 'get_inspection_cost', 'get_delivering_cost', \
        'get_additional_suggested_cost', 'direct_costs_sum', 'vat_amount', 'direct_costs_sum_with_vat', 'get_total_additional_cost',
        'get_final_cost', 'is_onsite_payment',
    ]

    def get_requesting_history(self, obj):
        requesting_history = obj.requesting_history
        change_url = reverse('admin:requestings_finisheddaangnrequestinghistory_change', args=(obj.requesting_history.id,))

        return mark_safe(f'<a href="{ change_url }">{ obj.requesting_history.id }</a>')

    get_requesting_history.allow_tags = True
    get_requesting_history.short_description = '의뢰번호'

    def get_queryset(self, obj):
        return DaangnRequestingSettlement.objects.all()

    def changelist_view(self, request, extra_context=None):
        view = super().changelist_view(request, extra_context=extra_context)
        view.context_data['title'] = '당근 의뢰 정산 목록'

        return view
