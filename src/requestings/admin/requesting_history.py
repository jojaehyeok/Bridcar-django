import locale
from urllib.parse import quote

from django import forms
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.forms import HiddenInput
from django.contrib.gis.measure import D
from django.contrib import admin, messages
from django.utils.safestring import mark_safe

from import_export.admin import ExportActionMixin, ExportActionModelAdmin, ImportExportModelAdmin

from nested_admin import NestedModelAdmin, NestedStackedInline

from dynamic_raw_id.admin import DynamicRawIDMixin

from rangefilter.filters import DateTimeRangeFilter

from requestings.models import RequestingHistory, RequestingSettlement, \
                                ExternalEvaluationTemplate, RequestingAdditionalCost, \
                                DeliveryResult, DeliveryAsset, CarBasicImage, CarAccidentSiteImage, \
                                Review, ReviewImage, BulkRequesting, DeliveryRegionDivision, DeliveryFeeRelation, \
                                RefererSettlement, FinishedRequestingHistory

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
from requestings.utils import generate_requesting_settlement_xlsx, get_agent_fee

from .common import requesting_history_path_getter, DisableModifyByRequestingStatusMixin


class RequestingAdditionalCostAdmin(NestedStackedInline):
    model = RequestingAdditionalCost
    min_num = 0
    extra = 0


class HiddenCarIDForm(forms.ModelForm):
    id = forms.CharField(max_length=30, widget=HiddenInput, required=False)

    class Meta:
        model = Car
        fields = '__all__'


@requesting_history_path_getter('car.requesting_history')
class CarEvaluationImageAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = CarEvaluationImage
    min_num = 0
    extra = 0


@requesting_history_path_getter('requesting_history')
class CarEvaluationResultAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = CarEvaluationResult
    min_num = 0
    extra = 0

    inlines = [
        CarEvaluationImageAdmin,
    ]


@requesting_history_path_getter('requesting_history')
class CarEvaluationSheetAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = CarEvaluationSheet
    min_num = 0
    extra = 0


@requesting_history_path_getter('requesting_history')
class CarhistoryResultAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = CarhistoryResult
    min_num = 0
    extra = 0


@requesting_history_path_getter('requesting_history')
class PerformanceCheckRecordAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = PerformanceCheckRecord
    min_num = 0
    extra = 0


class RequestingCarInlineAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = Car
    form = HiddenCarIDForm
    min_num = 1
    extra = 1
    can_delete = False

    inlines = [
        CarEvaluationResultAdmin,
        CarEvaluationSheetAdmin,
        CarhistoryResultAdmin,
        PerformanceCheckRecordAdmin,
    ]


@requesting_history_path_getter('requesting_history')
class CarBasicImageAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = CarBasicImage
    verbose_name = '기본 사진'
    verbose_name_plural = '기본 사진 목록'
    min_num = 0
    extra = 0


@requesting_history_path_getter('requesting_history')
class CarAccidentSiteImageAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = CarAccidentSiteImage
    verbose_name = '사고 부위 사진'
    verbose_name_plural = '사고 부위 사진 목록'
    min_num = 0
    extra = 0


class RequestingDeliveryResultAdmin(DisableModifyByRequestingStatusMixin, NestedStackedInline):
    model = DeliveryResult
    min_num = 0
    extra = 0

    inlines = [
        CarBasicImageAdmin,
        CarAccidentSiteImageAdmin,
    ]


@admin.register(RequestingHistory)
class RequestingHistoryAdmin(DynamicRawIDMixin, NestedModelAdmin):
    form = RequestingHistoryAdminForm

    inlines = [
        RequestingCarInlineAdmin,
        RequestingAdditionalCostAdmin,
        RequestingDeliveryResultAdmin,
    ]

    edit_fieldsets = (
        (
            '기본 내용', {
                'fields': (
                    'id', 'type', 'status', 'client', 'agent', 'deliverer', 'skip_fee_for_deliverer', 'external_client_name', \
                    'external_client_mobile_number', 'reservation_date', 'estimated_service_date', 'source_location', 'destination_location', \
                    'distance_between_source_destination', 'stopovers', 'memo',
                )
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

    readonly_fields = ( 'id', )

    add_form_template = 'requestings/admin/add_requesting_history_admin.html'
    change_list_template = 'requestings/admin/requesting_history_change_list.html'

    list_per_page = 30
    list_display = [
        'id', 'car_number', 'styled_type', 'styled_status', 'created_at', 'elapsed_time', 'reservation_date', 'source_location_address', 'destination_location_address', \
        'car_type', 'get_evaluation_cost', 'get_inspection_cost', 'get_delivering_cost', 'get_client', 'get_agent', 'get_deliverer',
    ]

    list_filter = ( 'type', RequestingHistoryStatusFilter, )

    dynamic_raw_id_fields = ( 'agent', 'client', 'deliverer', 'source_location', 'destination_location', 'fee_payment_histories', 'stopovers', )

    exclude = ( 'has_agent_delivery_start', )

    ordering = ( '-created_at', )

    actions = [ 'cancel_requesting', ]

    search_fields = ( 'car__number', )

    def get_queryset(self, obj):
        queryset = super(RequestingHistoryAdmin, self).get_queryset(obj)

        return queryset \
            .exclude(Q(status='DONE')) \
            .exclude(daangn_requesting_information__isnull=False)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return super(RequestingHistoryAdmin, self).get_fieldsets(request, obj)
        else:
            return self.edit_fieldsets

    def cancel_requesting(self, request, queryset):
        irrevocable_requestings = queryset \
            .exclude(
                Q(status='WAITING_WORKING')
            ) \
            .exclude(
                ~Q(type='ONLY_DELIVERY')& \
                Q(status='WAITING_DELIVERY_WORKING')
            ) \
            .exclude(
                Q(type='ONLY_DELIVERY')& \
                # 탁송이 이전된경우는 어떻게 환불을 시켜줘야할까..
                Q(is_delivery_transferred=False)& \
                Q(status='WAITING_DELIVERY_WORKING')
            )

        if len(irrevocable_requestings) > 0:
            messages.error(request, '취소가 불가능한 의뢰가 포함되어있습니다.')
            return

        for requesting_history in queryset:
            if requesting_history.type != 'ONLY_DELIVERY' and requesting_history.status == 'WAITING_DELIVERY_WORKING':
                requesting_history.status = 'WAITING_DELIVERER'

                if requesting_history.is_delivery_transferred == False:
                    requesting_history.is_delivery_transferred = True

                    total_additional_costs = requesting_history.additional_costs \
                        .filter(working_type='EVALUATION/INSPECTION')

                    settlement = RequestingSettlement.objects.create(
                        requesting_history=requesting_history,
                        user=requesting_history.agent,
                        evaluation_cost=requesting_history.evaluation_cost,
                        inspection_cost=requesting_history.inspection_cost,
                        is_onsite_payment=requesting_history.is_onsite_payment,
                    )

                    settlement.additional_costs.add(*total_additional_costs)
                elif requesting_history.deliverer != None:
                    requesting_history.deliverer = None
            else:
                for fee_payment_history in requesting_history.fee_payment_histories.all():
                    fee_payment_history.refund_fee()

                    if requesting_history.type == 'ONLY_DELIVERY':
                        requesting_history.status = 'WAITING_DELIVERER'
                    else:
                        requesting_history.status = 'WAITING_AGENT'

            requesting_history.save()

        messages.success(request, '의뢰가 취소되었습니다.')

    cancel_requesting.short_description = '의뢰 취소하기 (아직 시작되지 않은경우만 취소가능)'

    def source_location_address(self, obj):
        return f'{ obj.source_location.road_address } { obj.source_location.detail_address }'

    source_location_address.short_description = '출발지'

    def destination_location_address(self, obj):
        return f'{ obj.destination_location.road_address } { obj.destination_location.detail_address }'

    destination_location_address.short_description = '도착지'

    def styled_type(self, obj):
        text_color = ''
        type_string = dict(REQUESTING_TYPES)[obj.type]

        if obj.type == 'EVALUATION_DELIVERY':
            text_color = 'blue'
        elif obj.type == 'INSPECTION_DELIVERY':
            text_color = 'green'
        elif obj.type == 'ONLY_DELIVERY':
            text_color = '#ee3e61'

        return mark_safe(f'<span style="color: { text_color };">{ type_string }</span>')

    styled_type.short_description = '의뢰 형태'

    def styled_status(self, obj):
        image = None
        status_string = dict(REQUESTING_STATUS)[obj.status]

        if obj.status == 'WAITING_AGENT' or obj.status == 'WAITING_DELIVERER':
            image = '/statics/images/waiting.png'
        elif obj.status == 'DONE':
            image = '/statics/images/complete.png'
        elif obj.status == 'CANCELLED':
            image = '/statics/images/cancel.png'
        elif obj.status == 'DELIVERING' or obj.status == 'DELIVERING_DONE':
            image = '/statics/images/delivery.png'
        elif obj.status == 'WAITING_DELIVERY_WORKING':
            image = '/statics/images/delivery.png'
        elif obj.status == 'EVALUATING' or obj.status == 'EVALUATION_DONE':
            image = '/statics/images/inspection.png'

        if image is not None:
            return mark_safe(f'<div class="row"><img src="{ image }" style="width: 22px; height: 22px;"/>{ status_string }</div>')

        return status_string

    styled_status.short_description = '의뢰 상태'
    styled_status.admin_order_field = 'status'

    def car_type(self, obj):
        return obj.car.type

    car_type.short_description = '차종'

    def elapsed_time(self, obj):
        if obj.status == 'WAITING_AGENT' or obj.status == 'WAITING_DELIVERER':
            return obj.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')

        return '-'

    elapsed_time.short_description = '접수 경과시간'

    def car_number(self, obj):
        return obj.car.number

    car_number.allow_tags = True
    car_number.short_description = '차량번호'

    def get_evaluation_cost(self, obj):
        if obj.evaluation_cost:
            return f'{obj.evaluation_cost:,}원'

        return '-'

    get_evaluation_cost.short_description = '평가비'

    def get_inspection_cost(self, obj):
        if obj.inspection_cost:
            return f'{obj.inspection_cost:,}원'

        return '-'

    get_inspection_cost.short_description = '검수비'

    def get_delivering_cost(self, obj):
        if obj.delivering_cost:
            return f'{obj.delivering_cost:,}원'

        return '-'

    get_delivering_cost.short_description = '탁송비'

    def get_client(self, obj):
        if obj.client != None:
            change_url = reverse('admin:users_dealer_change', args=(obj.client.id,))
            return mark_safe(f'<a href="{ change_url }">{ obj.client.name }</a>')

        return '탈퇴한 유저'

    get_client.allow_tags = True
    get_client.short_description = '의뢰 고객'

    def get_agent(self, obj):
        if not obj.agent:
            return '-'
        else:
            change_url = reverse('admin:users_agent_change', args=(obj.agent.id,))
            return mark_safe(f'<a href="{ change_url }">{ obj.agent.name }</a>')

    get_agent.allow_tags = True
    get_agent.short_description = '담당 평카인'

    def get_deliverer(self, obj):
        if not obj.deliverer:
            return '-'
        else:
            change_url = reverse('admin:users_agent_change', args=(obj.deliverer.id,))
            return mark_safe(f'<a href="{ change_url }">{ obj.deliverer.name }</a>')

    get_deliverer.allow_tags = True
    get_deliverer.short_description = '담당 평카인'

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            kwargs['form'] = AddRequestingHistoryAdminForm
            kwargs['fields'] = [
                'car_number', 'type', 'client', 'agent', 'deliverer', 'source_location', \
                'destination_location', 'stopovers', 'evaluation_cost', 'inspection_cost', 'delivering_cost', \
                'additional_suggested_cost', 'fee', 'is_immediately_order', 'reservation_date', \
                'is_onsite_payment', 'memo',
            ]

        return super(RequestingHistoryAdmin, self).get_form(request, obj, **kwargs)

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj=None)

        if not obj:
            return []

        return inlines

    def save_model(self, request, obj, form, change):
        is_not_change = not change

        # 새로운 Object 가 아닐때 수수료 수취/회수 처리
        if change:
            original_agent = form.initial.get('agent', None)
            changed_agent = form.cleaned_data.get('agent', None)

            original_deliverer = form.initial.get('deliverer', None)
            changed_deliverer = form.cleaned_data.get('deliverer', None)

            if original_agent is None and changed_agent is not None:
                if obj.type != 'ONLY_DELIVERY':
                    fee = get_agent_fee(obj)

                    new_balance_history = BalanceHistory.objects.create(
                        user=obj.agent,
                        amount=fee,
                        type='fee_escrow',
                        sub_type='agent',
                    )

                    obj.fee_payment_histories.add(new_balance_history)
            elif original_agent != changed_agent:
                if original_agent is not None:
                    fee_payment_histories = obj.fee_payment_histories \
                        .filter(
                            Q(user=original_agent)& \
                            Q(type='fee_escrow')& \
                            Q(sub_type='agent')
                        )

                    [ history.refund_fee() for history in fee_payment_histories ]

            if original_deliverer is None and changed_deliverer is not None:
                fee = get_agent_fee(obj)

                if not obj.skip_fee_for_deliverer:
                    new_balance_history = BalanceHistory.objects.create(
                        user=obj.deliverer,
                        amount=fee,
                        type='fee_escrow',
                        sub_type='deliverer',
                    )

                    obj.fee_payment_histories.add(new_balance_history)
            elif original_deliverer != changed_deliverer:
                if original_deliverer is not None:
                    fee_payment_histories = obj.fee_payment_histories \
                        .filter(
                            Q(user=original_deliverer)& \
                            Q(type='fee_escrow')& \
                            Q(sub_type='deliverer')
                        )

                    [ history.refund_fee() for history in fee_payment_histories ]

            obj.save()
        else:
            if obj.agent is not None or obj.deliverer is not None:
                new_balance_history = BalanceHistory.objects.create(
                    user=obj.agent if obj.type != 'ONLY_DELIVERY' else obj.deliverer,
                    amount=form.cleaned_data['fee'],
                    type='fee_escrow',
                    sub_type='agent' if obj.type != 'ONLY_DELIVERY' else 'deliverer',
                )

                obj.save()
                obj.fee_payment_histories.add(new_balance_history)

        if is_not_change:
            car_number = form.cleaned_data['car_number']
            requesting_type = form.cleaned_data.get('type')
            agent = form.cleaned_data.get('agent', None)
            deliverer = form.cleaned_data.get('deliverer', None)

            if requesting_type == 'ONLY_DELIVERY':
                if deliverer is not None:
                    obj.status = 'WAITING_DELIVERY_WORKING'
                else:
                    obj.status = 'WAITING_DELIVERER'
            elif requesting_type == 'EVALUATION_DELIVERY' or requesting_type == 'INSPECTION_DELIVERY':
                if agent is not None:
                    obj.status = 'WAITING_WORKING'
                else:
                    obj.status = 'WAITING_AGENT'

            super(RequestingHistoryAdmin, self).save_model(request, obj, form, change)

            Car.objects.create(
                number=car_number,
                requesting_history=obj,
            )

        else:
            obj.distance_between_source_destination = get_driving_distance_with_kakao(
                { 'latitude': obj.source_location.coord[1], 'longitude': obj.source_location.coord[0], },
                { 'latitude': obj.destination_location.coord[1], 'longitude': obj.destination_location.coord[0], },
            )

            obj.save()

        '''
        if is_not_change and (obj.status == 'WAITING_AGENT' or obj.status == 'WAITING_DELIVERER'):
            close_agents = Agent.objects \
                .filter(
                    Q(agent_profile__isnull=False)& \
                    Q(agent_location__using_auto_dispatch=True)& \
                    Q(agent_location__is_end_of_work=False)& \
                    Q(
                        agent_location__coord__distance_lte=(
                            obj.source_location.coord,
                            D(km=2)
                        )
                    )
                )

            if close_agents.count() > 0:
                Notification.create(
                    'USER',
                    'CREATE_REQUESTING',
                    user=close_agents,
                    actor=obj.client,
                    requesting_history=obj,
                    data=obj
                )
        '''

        original_reservation_date = form.initial.get('reservation_date', None)
        new_reservation_date = form.cleaned_data.get('reservation_date', None)

        modified_fields_for_daangn = []

        if change and original_reservation_date != new_reservation_date and \
            hasattr(obj, 'daangn_requesting_information'):
            modified_fields_for_daangn.append('reservation_date')

        original_estimated_service_date = form.initial.get('estimated_service_date', None)
        estimated_service_date = form.cleaned_data.get('estimated_service_date', None)

        if change and original_estimated_service_date != estimated_service_date and \
            hasattr(obj, 'daangn_requesting_information'):
            modified_fields_for_daangn.append('estimated_service_date')

        original_deliverer = form.initial.get('deliverer', None)
        deliverer = form.cleaned_data.get('deliverer', None)

        if original_deliverer is None and deliverer is not None:
            webhook_sender = DaangnRequestingWebhookSender(
                obj.hook_url,
                requesting_id=obj.id,
                reason='REQUESTING_AGENT_APPLIED',
            )

            webhook_sender.start()

        if change and hasattr(obj, 'daangn_requesting_information'):
            webhook_sender = DaangnRequestingWebhookSender(
                obj.hook_url,
                requesting_id=obj.id,
                reason='REQUESTING_INFORMATION_MODIFIED_FROM_ADMIN',
                extra={
                    'fields': modified_fields_for_daangn,
                }
            )

            webhook_sender.start()

    def save_related(self, request, form, formsets, change):
        for formset in formsets:
            self.save_formset(request, form, formset, change=change)


@admin.register(FinishedRequestingHistory)
class FinishedRequestingHistoryAdmin(admin.ModelAdmin):
    def get_queryset(self, obj):
        queryset = super(FinishedRequestingHistoryAdmin, self).get_queryset(obj)

        return queryset \
            .filter(Q(status='DONE')) \
            .exclude(daangn_requesting_information__isnull=False)

    def has_add_permission(self, obj):
        return False


@admin.register(RequestingSettlement)
class RequestingSettlementAdmin(admin.ModelAdmin):
    resource_class = RequestingSettlementResource

    list_per_page = 30
    list_display = [
        'id', 'get_requesting_history', 'requesting_type', 'requesting_history_created_at', 'requesting_end_at', 'source_location_address',
        'destination_location_address', 'car_type', 'car_number', 'get_evaluation_cost', 'get_inspection_cost', 'get_delivering_cost', \
        'get_additional_suggested_cost', 'direct_costs_sum', 'vat_amount', 'direct_costs_sum_with_vat', 'get_total_additional_cost',
        'get_final_cost', 'is_onsite_payment',
    ]

    list_filter = (
        ( 'requesting_end_at', DateTimeRangeFilter, ),
        RequestingSettlementClientNameInputFilter,
        RequestingSettlementClientCompanyNameInputFilter,
        RequestingSettlementAdminProfileIdInputFilter,
    )

    search_fields = (
        'requesting_history__client__id',
        'requesting_history__client__name',
        'requesting_history__client__dealer_profile__company_name',
    )

    raw_id_fields = ( 'user', 'requesting_history', )

    actions = [ 'export_as_xlsx', ]

    '''
    def get_export_filename(self, request, queryset, file_format):
        return '{0}.{1}'.format(
            quote('정산내역'.encode('utf-8')),
            file_format.get_extension()
        )
    '''

    def has_change_permission(self, request, obj=None):
        return False

    def export_as_xlsx(self, request, queryset):
        xlsx_output = generate_requesting_settlement_xlsx(queryset)

        filename = '정산목록.xlsx'
        response = HttpResponse(
            xlsx_output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(quote(filename.encode('utf-8')))

        return response

    export_as_xlsx.short_description = '선택 목록 엑셀로 출력하기'

    def requesting_history_created_at(self, obj):
        return obj.requesting_history.created_at

    requesting_history_created_at.short_description = '의뢰 접수 일시'

    def get_requesting_history(self, obj):
        requesting_history = obj.requesting_history
        change_url = reverse('admin:requestings_finishedrequestinghistory_change', args=(obj.requesting_history.id,))

        return mark_safe(f'<a href="{ change_url }">{ obj.requesting_history.id }</a>')

    get_requesting_history.allow_tags = True
    get_requesting_history.short_description = '의뢰번호'

    def requesting_type(self, obj):
        return dict(REQUESTING_TYPES)[obj.requesting_history.type]

    requesting_type.short_description = '의뢰 구분'

    def source_location_address(self, obj):
        return f'{ obj.requesting_history.source_location.road_address } { obj.requesting_history.source_location.detail_address }'

    source_location_address.short_description = '출발지'

    def destination_location_address(self, obj):
        return f'{ obj.requesting_history.destination_location.road_address } { obj.requesting_history.destination_location.detail_address }'

    destination_location_address.short_description = '도착지'

    def car_type(self, obj):
        return obj.requesting_history.car.type

    car_type.short_description = '차종'

    def car_number(self, obj):
        return obj.requesting_history.car.number

    car_number.allow_tags = True
    car_number.short_description = '차량번호'

    def get_evaluation_cost(self, obj):
        if obj.evaluation_cost:
            return f'{obj.evaluation_cost:,}원'

        return '-'

    get_evaluation_cost.short_description = '평가비'

    def get_inspection_cost(self, obj):
        if obj.inspection_cost:
            return f'{obj.inspection_cost:,}원'

        return '-'

    get_inspection_cost.short_description = '검수비'

    def get_delivering_cost(self, obj):
        if obj.delivering_cost:
            return f'{obj.delivering_cost:,}원'

        return '-'

    get_delivering_cost.short_description = '탁송비'

    def get_additional_suggested_cost(self, obj):
        if obj.additional_suggested_cost:
            return f'{obj.additional_suggested_cost:,}원'

        return '-'

    get_additional_suggested_cost.short_description = '추가 제안 요금'

    def direct_costs_sum(self, obj):
        return f'{obj.direct_costs:,}원'

    direct_costs_sum.short_description = '소계 (공급가액)'

    def vat_amount(self, obj):
        return f'{obj.vat:,}원'

    vat_amount.short_description = 'vat'

    def direct_costs_sum_with_vat(self, obj):
        return f'{obj.direct_costs + obj.vat:,}원'

    direct_costs_sum_with_vat.short_description = '공급가액 합계'

    def get_total_additional_cost(self, obj):
        return f'{obj.total_additional_cost:,}원'

    get_total_additional_cost.short_description = '기타금액 합계'

    def get_client(self, obj):
        client = obj.requesting_history.client

        if client == None:
            return '탈퇴한 유저'

        client_name = client.name

        if client.dealer_profile.company_name != None:
            client_name += f' ({ client.dealer_profile.company_name })'

        change_url = reverse('admin:users_dealer_change', args=(client.id,))
        return mark_safe(f'<a href="{ change_url }">{ client_name }</a>')

    get_client.short_description = '의뢰 고객'

    def get_agent(self, obj):
        agent = obj.requesting_history.agent

        if agent == None:
            return '해당없음'

        change_url = reverse('admin:users_agent_change', args=(agent.id,))
        return mark_safe(f'<a href="{ change_url }">{ agent.name }</a>')

    get_agent.short_description = '담당 평카인'

    def get_deliverer(self, obj):
        deliverer = obj.requesting_history.deliverer

        if deliverer == None:
            return ''

        change_url = reverse('admin:users_agent_change', args=(deliverer.id,))
        return mark_safe(f'<a href="{ change_url }">{ deliverer.name }</a>')

    get_deliverer.short_description = '담당 탁송기사'

    def get_final_cost(self, obj):
        return f'{ "{:,}".format(obj.total_cost) }원'

    get_final_cost.short_description = '청구 금액'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = '의뢰 정산 목록'

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(RefererSettlement)
class RefererSettlementAdmin(admin.ModelAdmin):
    list_display = ( 'settlement_id', 'get_requesting_history', 'get_agent', 'revenue_amount', )

    raw_id_fields = ( 'user', 'requesting_history', )

    def settlement_id(self, obj):
        return obj.pk

    settlement_id.short_description = '정산 번호'

    def get_requesting_history(self, obj):
        if obj.requesting_history == None:
            return '-'

        change_url = reverse('admin:requestings_requestinghistory_change', args=(obj.requesting_history.id,))
        return mark_safe(f'<a href="{ change_url }">{ obj.requesting_history.id }</a>')

    get_requesting_history.allow_tags = True
    get_requesting_history.short_description = '해당 의뢰번호'

    def revenue_amount(self, obj):
        return f'{obj.revenue:,}원'

    revenue_amount.short_description = '홍보비 정산 금액'

    def get_agent(self, obj):
        change_url = reverse('admin:users_agent_change', args=(obj.user.id,))
        return mark_safe(f'<a href="{ change_url }">{ obj.user.name }</a>')

    get_agent.allow_tags = True
    get_agent.short_description = '해당 평카인'


@admin.register(ExternalEvaluationTemplate)
class ExternalEvaluationTemplateAdmin(admin.ModelAdmin):
    pass


@admin.register(DeliveryAsset)
class DeliveryAssetAdmin(NestedModelAdmin):
    pass


class ReviewImageAdmin(admin.StackedInline):
    model = ReviewImage
    verbose_name = '리뷰 사진'
    verbose_name_plural = '리뷰 사진 목록'
    min_num = 0
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ( 'created_at', 'get_requesting_history', 'content', 'is_exposing_to_dealer', )

    inlines = [
        ReviewImageAdmin,
    ]

    def get_requesting_history(self, obj):
        if obj.requesting_history == None:
            return '-'

        change_url = reverse('admin:requestings_requestinghistory_change', args=(obj.requesting_history.id,))
        return mark_safe(f'<a href="{ change_url }">{ obj.requesting_history.id }</a>')

    get_requesting_history.allow_tags = True
    get_requesting_history.short_description = '해당 의뢰번호'


@admin.register(BulkRequesting)
class BulkRequestingAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'created_at', 'client', 'is_processed', )

    raw_id_fields = ( 'client', )


@admin.register(DeliveryRegionDivision)
class DeliveryRegionDivisionAdmin(admin.ModelAdmin):
    search_fields = ( 'address_name', )


@admin.register(DeliveryFeeRelation)
class DeliveryFeeRelationAdmin(admin.ModelAdmin):
    list_display = ( 'pk', 'departure_region_division', 'arrival_region_division', 'delivery_fee', )

    autocomplete_fields = ( 'departure_region_division', 'arrival_region_division' )
