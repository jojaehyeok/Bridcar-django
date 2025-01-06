from django.db.models import Q
from django.contrib.gis.measure import D

from users.models import Agent

from requestings.models import RequestingHistory, RequestingSettlement, DeliveryResult, \
                                DeliveryFeeRelation

from locations.utils import distance_to_decimal_degrees, search_road_address_from_kakao

from notifications.models import Notification


def handover_delivery(requesting_history, current_agent=None):
    requesting_history.status = 'WAITING_DELIVERER'
    requesting_history.deliverer = None
    requesting_history.is_delivery_transferred = True
    requesting_history.estimated_service_date = None

    requesting_history.save()

    total_additional_costs = requesting_history.additional_costs \
        .filter(working_type='EVALUATION/INSPECTION')

    settlement = RequestingSettlement.objects.create(
        requesting_history=requesting_history,
        user=requesting_history.agent,
        evaluation_cost=requesting_history.evaluation_cost,
        inspection_cost=requesting_history.inspection_cost,
        is_onsite_payment=requesting_history.is_onsite_payment,
    )

    if requesting_history.type == 'EVALUATION_DELIVERY':
        requesting_history.agent.agent_profile.total_evaluation_count += 1
    elif requesting_history.type == 'INSPECTION_DELIVERY':
        requesting_history.agent.agent_profile.total_inspection_count += 1

    requesting_history.agent.agent_profile.save()

    settlement.additional_costs.add(*total_additional_costs)

    if current_agent != None:
        close_agents = Agent.objects \
            .filter(
                Q(agent_profile__isnull=False)& \
                Q(agent_location__using_auto_dispatch=True)& \
                Q(agent_location__is_end_of_work=False)& \
                Q(
                    agent_location__coord__distance_lte=(
                        requesting_history.source_location.coord,
                        D(km=2)
                    )
                )
            ) \
            .exclude(pk=current_agent.pk)

        if close_agents.count() > 0:
            Notification.create(
                'USER',
                'CREATE_REQUESTING',
                user=close_agents,
                actor=requesting_history.client,
                requesting_history=requesting_history,
                data=requesting_history,
            )


def get_delivery_cost(source_road_address='', destination_road_address=''):
    delivery_fee_relation = None

    if source_road_address and destination_road_address:
        source_road_address_result = search_road_address_from_kakao(source_road_address)
        destination_road_address_result = search_road_address_from_kakao(destination_road_address)

        splited_source_road_address_region_name = source_road_address_result['address']['region_2depth_name'].split(' ')

        source_road_address_combined_2depth = \
            (
                source_road_address_result['address']['region_1depth_name'] + ' ' + \
                splited_source_road_address_region_name[0]
            ).strip()

        source_road_address_combined_3depth = \
            (
                source_road_address_result['address']['region_1depth_name'] + ' ' + \
                source_road_address_result['address']['region_2depth_name'] + ' ' + \
                source_road_address_result['address']['region_3depth_name']
            ).strip()

        splited_destination_road_address_region_name = destination_road_address_result['address']['region_2depth_name'].split(' ')

        destination_road_address_combined_2depth = \
            (
                destination_road_address_result['address']['region_1depth_name'] + ' ' + \
                splited_destination_road_address_region_name[0]
            ).strip()

        destination_road_address_combined_3depth = \
            (
                destination_road_address_result['address']['region_1depth_name'] + ' ' + \
                destination_road_address_result['address']['region_2depth_name'] + ' ' + \
                destination_road_address_result['address']['region_3depth_name']
            ).strip()

        # 출발지의 시 / 구(법정동) 와 도착지의 시 / 구(법정동) 으로 검색
        # 먼저, 좁은 범위의 지역 부터 검색 - 인천광역시의 경우 영종도와 다른 행정구역간 요금이 상이한 경우가 있기때문
        delivery_fee_relation = DeliveryFeeRelation.objects \
            .filter(
                (
                    Q(departure_region_division__address_name__contains=source_road_address_combined_3depth)
                )& \
                (
                    Q(arrival_region_division__address_name__contains=destination_road_address_combined_2depth)| \
                    Q(arrival_region_division__address_name__contains=destination_road_address_combined_3depth)
                )
            ) \
            .first()

        if delivery_fee_relation is None:
            delivery_fee_relation = DeliveryFeeRelation.objects \
                .filter(
                    (
                        Q(departure_region_division__address_name__contains=source_road_address_combined_2depth)
                    )& \
                    (
                        Q(arrival_region_division__address_name__contains=destination_road_address_combined_2depth)| \
                        Q(arrival_region_division__address_name__contains=destination_road_address_combined_3depth)
                    )
                ) \
                .first()

        if delivery_fee_relation is None:
            # 위 검색 결과가 없으면 반대로 검색
            # 여기도 마찬가지로 좁은 범위의 지역 부터 검색
            delivery_fee_relation = DeliveryFeeRelation.objects \
                .filter(
                    (
                        Q(departure_region_division__address_name__contains=destination_road_address_combined_3depth)
                    )& \
                    (
                        Q(arrival_region_division__address_name__contains=source_road_address_combined_2depth)| \
                        Q(arrival_region_division__address_name__contains=source_road_address_combined_3depth)
                    )
                ) \
                .first()

        if delivery_fee_relation is None:
            delivery_fee_relation = DeliveryFeeRelation.objects \
                .filter(
                    (
                        Q(departure_region_division__address_name__contains=destination_road_address_combined_2depth)
                    )& \
                    (
                        Q(arrival_region_division__address_name__contains=source_road_address_combined_2depth)| \
                        Q(arrival_region_division__address_name__contains=source_road_address_combined_3depth)
                    )
                ) \
                .first()

    if delivery_fee_relation != None:
        return delivery_fee_relation.delivery_fee

    return 0
