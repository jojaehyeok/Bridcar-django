from requestings.models import RequestingSettlement


def create_requesting_settlement(requesting_history):
    if requesting_history.is_delivery_transferred == True:
        total_additional_costs = requesting_history.additional_costs \
            .filter(working_type='DELIVERY')

        settlement = RequestingSettlement.objects.create(
            requesting_history=requesting_history,
            user=requesting_history.deliverer,
            delivering_cost=requesting_history.delivering_cost + (requesting_history.stopovers.count() * 5000),
            additional_suggested_cost=requesting_history.additional_suggested_cost,
            is_onsite_payment=requesting_history.is_onsite_payment,
        )

        requesting_history.deliverer.agent_profile.total_delivery_count += 1
        requesting_history.deliverer.agent_profile.save()

        settlement.additional_costs.add(*total_additional_costs)
    else:
        settlement_user = requesting_history.deliverer if requesting_history.type == 'ONLY_DELIVERY' \
            else requesting_history.agent

        total_additional_costs = requesting_history.additional_costs.all()

        settlement = RequestingSettlement.objects.create(
            requesting_history=requesting_history,
            user=settlement_user,
            evaluation_cost=requesting_history.evaluation_cost,
            inspection_cost=requesting_history.inspection_cost,
            delivering_cost=requesting_history.delivering_cost + (requesting_history.stopovers.count() * 5000),
            additional_suggested_cost=requesting_history.additional_suggested_cost,
            is_onsite_payment=requesting_history.is_onsite_payment,
        )

        settlement.additional_costs.add(*total_additional_costs)

        settlement_user.agent_profile.total_delivery_count += 1

        if requesting_history.type == 'INSPECTION_DELIVERY':
            settlement_user.agent_profile.total_inspection_count += 1
        elif requesting_history.type == 'EVALUATION_DELIVERY':
            settlement_user.agent_profile.total_evaluation_count += 1

        settlement_user.agent_profile.save()

    requesting_history.status = 'DONE'
    requesting_history.save()
