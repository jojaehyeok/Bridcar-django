def get_agent_fee(requesting_history):
    fee = 0

    try:
        if requesting_history.is_delivery_transferred == True:
            fee = (
                (requesting_history.delivering_cost or 0) + (requesting_history.additional_suggested_cost or 0) + \
                (requesting_history.stopovers.count() * 5000)
            ) * 0.2
        else:
            fee = requesting_history.total_cost * 0.2
    except:
        return fee

    return fee
