from django import forms
from django.forms import widgets

from requestings.constants import REQUESTING_TYPES, DELIVERY_REQUESTING_STATUS
from requestings.utils import get_agent_fee


class RequestingHistoryAdminForm(forms.ModelForm):
    def clean_agent(self):
        type = self.cleaned_data['type']
        agent = self.cleaned_data.get('agent', None)

        if type == 'EVALUATION_DELIVERY' or type == 'INSPECTION_DELIVERY':
            if agent is None:
                raise forms.ValidationError('담당 평카인을 선택해주세요')

        if self.initial.get('agent') is None and agent is not None:
            if self.instance.type != 'ONLY_DELIVERY':
                fee = get_agent_fee(self.instance)

                if agent.agent_profile.balance - fee < 0:
                    raise forms.ValidationError(f'에이전트의 예치금이 부족합니다. (발생 수수료: { int(fee) }원)')

        return agent

    def clean_deliverer(self):
        type = self.cleaned_data['type']
        status = self.cleaned_data.get('status', None)
        deliverer = self.cleaned_data.get('deliverer', None)

        if type == 'ONLY_DELIVERY' and (status != 'WAITING_DELIVERER' and status != None) and deliverer is None:
            raise forms.ValidationError('담당 탁송기사를 선택해주세요')

        if self.initial.get('deliverer', None) is None and deliverer is not None:
            fee = get_agent_fee(self.instance)

            if deliverer.agent_profile.balance - fee < 0:
                raise forms.ValidationError(f'에이전트의 예치금이 부족합니다. (발생 수수료: { int(fee) }원)')

        return deliverer


class DaangnRequestingHistoryAdminForm(forms.ModelForm):
    type = forms.ChoiceField(
        label='의뢰 형태',
        choices=REQUESTING_TYPES[2:],
    )

    status = forms.ChoiceField(
        label='의뢰 상태',
        choices=DELIVERY_REQUESTING_STATUS,
    )

    daangn_requesting_information_is_paid = forms.BooleanField(
        required=False,
        label='(당근) 확정 여부',
    )

    daangn_requesting_information_is_forced_exposure = forms.BooleanField(
        required=False,
        label='확정 무관 강제 노출 여부',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        requesting_history = self.instance

        if hasattr(requesting_history, 'daangn_requesting_information'):
            self.is_daangn_requesting_history = True

            self.fields['daangn_requesting_information_is_paid'].initial = requesting_history.daangn_requesting_information.is_paid
            self.fields['daangn_requesting_information_is_forced_exposure'].initial = requesting_history.daangn_requesting_information.is_forced_exposure

        if hasattr(self.fields, 'client'):
            self.fields['client'].required = True

    def save(self, commit=True):
        if self.is_daangn_requesting_history:
            daangn_requesting_information_is_paid = self.cleaned_data.get('daangn_requesting_information_is_paid', None)
            daangn_requesting_information_is_forced_exposure = self.cleaned_data.get('daangn_requesting_information_is_forced_exposure', None)

            self.instance.daangn_requesting_information.is_paid = daangn_requesting_information_is_paid
            self.instance.daangn_requesting_information.is_forced_exposure = daangn_requesting_information_is_forced_exposure
            self.instance.daangn_requesting_information.save()

        return super(DaangnRequestingHistoryAdminForm, self).save(commit=commit)

    def clean_agent(self):
        type = self.cleaned_data['type']
        agent = self.cleaned_data['agent']

        if type == 'EVALUATION_DELIVERY' or type == 'INSPECTION_DELIVERY':
            if agent is None:
                raise forms.ValidationError('담당 평카인을 선택해주세요')

        return agent

    def clean_deliverer(self):
        type = self.cleaned_data['type']
        status = self.cleaned_data.get('status', None)
        deliverer = self.cleaned_data['deliverer']

        if type == 'ONLY_DELIVERY' and (status != 'WAITING_DELIVERER' and status != None) and deliverer is None:
            raise forms.ValidationError('담당 탁송기사를 선택해주세요')

        return deliverer

    def clean_reservation_date(self):
        requesting_history = self.instance

        reservation_date = self.cleaned_data.get('reservation_date', None)

        if hasattr(requesting_history, 'daangn_requesting_information'):
            daangn_initial_reservation_date = \
                requesting_history.daangn_requesting_information.initial_reservation_date

            if daangn_initial_reservation_date is not None and reservation_date is not None:
                if requesting_history.daangn_requesting_information.is_paid is not True:
                    if daangn_initial_reservation_date > reservation_date:
                        raise forms.ValidationError('[당근의뢰] 예약 일자는 초기 설정값 보다 과거로 설정 할 수 없습니다.')

        return reservation_date


class RequestingHistoryFeeWidget(widgets.TextInput):
    template_name = 'requestings/widget/requesting_history_fee.html'


class AddRequestingHistoryAdminForm(RequestingHistoryAdminForm):
    car_number = forms.CharField(
        label='차량 번호',
        widget=forms.TextInput(attrs={'placeholder': '55가 6566'})
    )

    fee = forms.IntegerField(
        label='수수료',
        widget=RequestingHistoryFeeWidget(),
    )

    is_immediately_order = forms.BooleanField(
        label='즉시 오더 여부',
        initial=True,
        required=False,
    )

    def clean_fee(self):
        type = self.cleaned_data['type']
        agent = self.cleaned_data['agent']
        fee = self.cleaned_data['fee']

        if type == 'ONLY_DELIVERY':
            initial_deliverer = self.initial.get('deliverer', None)
            deliverer = self.cleaned_data.get('deliverer', None)

            if deliverer is not None and initial_deliverer != deliverer:
                if deliverer.agent_profile.balance - fee < 0:
                    raise forms.ValidationError(f'담당 탁송기사분의 보유 금액이 부족합니다.')
        else:
            if agent.agent_profile.balance - fee < 0:
                raise forms.ValidationError('담당 평카인분의 보유 금액이 부족합니다.')

        return fee

    def clean_reservation_date(self):
        reservation_date = self.cleaned_data['reservation_date']
        is_immediately_order = self.cleaned_data['is_immediately_order']

        if not is_immediately_order:
            if reservation_date is None:
                raise forms.ValidationError('즉시 오더가 아닌경우 예약 날짜가 설정되어야 합니다.')

        return reservation_date
