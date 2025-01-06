from pytz import timezone
from django.db.models import F, Sum

from import_export import resources
from import_export import widgets
from import_export.fields import Field

from requestings.constants import REQUESTING_TYPES


class RequestingSettlementResource(resources.ModelResource):
    requesting_settlement_id = Field(attribute='pk', column_name='정산번호')
    requesting_id = Field(attribute='requesting_history__id', column_name='의뢰번호')
    requesting_type = Field(attribute='requesting_type', column_name='의뢰구분')
    requesting_created_at = Field(attribute='requesting_created_at', column_name='의뢰 접수 일시')
    requesting_end_at = Field(attribute='requesting_end_at', column_name='의뢰 완료 일자')
    source_address = Field(attribute='source_address', column_name='출발지')
    destination_address = Field(attribute='destination_address', column_name='도착지')
    evaluation_cost = Field(attribute='evaluation_cost', column_name='평가비', widget=widgets.NumberWidget())
    inspection_cost = Field(attribute='inspection_cost', column_name='검수비', widget=widgets.NumberWidget())
    delivering_cost = Field(attribute='delivering_cost', column_name='탁송비', widget=widgets.NumberWidget())
    additional_suggested_cost = Field(attribute='additional_suggested_cost', column_name='추가 제안 요금', widget=widgets.NumberWidget())
    direct_costs_sum = Field(attribute='direct_costs_sum', column_name='소계 (공급가액)', widget=widgets.NumberWidget())
    fuel_costs = Field(attribute='fuel_costs', column_name='주유비', widget=widgets.NumberWidget())
    vat_amount = Field(attribute='vat_amount', column_name='VAT', widget=widgets.NumberWidget())
    direct_costs_sum_with_vat = Field(attribute='direct_costs_sum_with_vat', column_name='공급가액 합계', widget=widgets.NumberWidget())
    total_additional_cost = Field(attribute='total_additional_cost', column_name='기타 비용 합계', widget=widgets.NumberWidget())
    final_cost = Field(attribute='final_cost', column_name='청구 금액', widget=widgets.NumberWidget())

    #client = Field(attribute='client', column_name='의뢰인')
    #agent = Field(attribute='agent', column_name='평카인')
    #deliverer = Field(attribute='deliverer', column_name='탁송기사')

    def dehydrate_requesting_created_at(self, settlement):
        return settlement.requesting_history.created_at.astimezone(timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일 %H시 %M분')

    def dehydrate_requesting_end_at(self, settlement):
        return settlement.requesting_end_at.astimezone(timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일 %H시 %M분')

    def dehydrate_requesting_type(self, settlement):
        return dict(REQUESTING_TYPES)[settlement.requesting_history.type]

    def dehydrate_client(self, settlement):
        if settlement.requesting_history.client == None:
            return '탈퇴한 유저'

        return f'{ settlement.requesting_history.client.name } ({ settlement.requesting_history.client.id })'

    def dehydrate_agent(self, settlement):
        if settlement.requesting_history.agent == None:
            return '해당 없음'
        else:
            return f'{ settlement.requesting_history.agent.name } ({ settlement.requesting_history.agent.id })'

    def dehydrate_source_address(self, settlement):
        return f'{ settlement.requesting_history.source_location.road_address } { settlement.requesting_history.source_location.detail_address }'

    def dehydrate_destination_address(self, settlement):
        return f'{ settlement.requesting_history.destination_location.road_address } { settlement.requesting_history.destination_location.detail_address }'

    def dehydrate_deliverer(self, settlement):
        if settlement.requesting_history.deliverer == None:
            return '해당 없음'
        else:
            return f'{ settlement.requesting_history.deliverer.name } ({ settlement.requesting_history.deliverer.id })'

    def dehydrate_final_cost(self, settlement):
        return '{:,}'.format(settlement.total_cost)

    def dehydrate_evaluation_cost(self, settlement):
        return '{:,}'.format(settlement.evaluation_cost)

    def dehydrate_inspection_cost(self, settlement):
        return '{:,}'.format(settlement.inspection_cost)

    def dehydrate_delivering_cost(self, settlement):
        return '{:,}'.format(settlement.delivering_cost)

    def dehydrate_additional_suggested_cost(self, settlement):
        return '{:,}'.format(settlement.additional_suggested_cost)

    def dehydrate_total_additional_cost(self, settlement):
        return '{:,}'.format(settlement.total_additional_cost)

    def dehydrate_direct_costs_sum(self, settlement):
        return f'{settlement.direct_costs:,}'

    def dehydrate_fuel_costs(self, settlement):
        return f'{settlement.fuel_costs:,}'

    def dehydrate_vat_amount(self, settlement):
        return '{:,}'.format(settlement.vat)

    def dehydrate_direct_costs_sum_with_vat(self, settlement):
        return f'{settlement.direct_costs + settlement.vat:,}'

    def after_export(self, queryset, data, *args, **kwargs):
        evaluation_cost_sum = 0
        inspection_cost_sum = 0
        delivering_cost_sum = 0
        additional_suggested_cost_sum = 0
        direct_costs_sum = 0
        fuel_costs_sum = 0
        vat_sum = 0
        direct_costs_sum_with_vat_sum = 0
        total_additional_cost_sum = 0
        total_cost_sum = 0

        for settlement in queryset:
            evaluation_cost_sum += settlement.evaluation_cost
            inspection_cost_sum += settlement.inspection_cost
            delivering_cost_sum += settlement.delivering_cost
            additional_suggested_cost_sum += settlement.additional_suggested_cost
            direct_costs_sum += settlement.direct_costs
            fuel_costs_sum += settlement.fuel_costs
            vat_sum += settlement.vat
            direct_costs_sum_with_vat_sum += (settlement.direct_costs + settlement.vat)
            total_additional_cost_sum += settlement.total_additional_cost
            total_cost_sum += settlement.total_cost

        data.append([
            '',
            '',
            '',
            '',
            '',
            '',
            '계',
            f'{evaluation_cost_sum:,}',
            f'{inspection_cost_sum:,}',
            f'{delivering_cost_sum:,}',
            f'{additional_suggested_cost_sum:,}',
            f'{direct_costs_sum:,}',
            f'{fuel_costs_sum:,}',
            f'{vat_sum:,}',
            f'{direct_costs_sum_with_vat_sum:,}',
            f'{total_additional_cost_sum:,}',
            f'{total_cost_sum:,}',
        ])
