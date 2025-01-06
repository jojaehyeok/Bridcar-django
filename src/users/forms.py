from django import forms
from django.db.models import Q
from django.forms import widgets
from django.utils.translation import gettext as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from users.models import Agent, Dealer


class AgentAdminAddForm(forms.ModelForm):

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']

        if mobile_number is '':
            return mobile_number

        try:
            Agent.objects.get(Q(mobile_number=mobile_number))

            raise forms.ValidationError('해당 핸드폰번호를 사용하고 있는 평가사가 존재합니다')
        except Agent.DoesNotExist:
            pass

        return mobile_number


class AgentProfileAdminForm(forms.ModelForm):
    def has_changed(self, *args, **kwargs):
        if not self.instance.pk:
            return True

        return super(AgentProfileAdminForm, self).has_changed(*args, **kwargs)


class AgentAdminForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        initial_mobile_number = self.initial.get('mobile_number', None)

        if mobile_number is '':
            return mobile_number

        if mobile_number != initial_mobile_number:
            try:
                Agent.objects.get(Q(mobile_number=mobile_number))

                raise forms.ValidationError('해당 핸드폰번호를 사용하고 있는 평가사가 존재합니다')
            except Agent.DoesNotExist:
                pass

        return mobile_number


class DealerAdminAddForm(forms.ModelForm):
    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']

        if mobile_number is '':
            return mobile_number

        try:
            Dealer.objects.get(Q(mobile_number=mobile_number))

            raise forms.ValidationError('해당 핸드폰번호를 사용하고 있는 딜러가 존재합니다')
        except Dealer.DoesNotExist:
            pass

        return mobile_number


class DealerAdminForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data['mobile_number']
        initial_mobile_number = self.initial.get('mobile_number', None)

        if mobile_number is '':
            return mobile_number

        if mobile_number != initial_mobile_number:
            try:
                Dealer.objects.get(Q(mobile_number=mobile_number))

                raise forms.ValidationError('해당 핸드폰번호를 사용하고 있는 딜러가 존재합니다')
            except Dealer.DoesNotExist:
                pass

        return mobile_number
