from urllib.parse import quote

from django.urls import path
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.contrib.gis import forms as gis_forms
from django.contrib.auth import admin as auth_admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, AdminPasswordChangeForm
from django.db.models import Q

from dynamic_raw_id.admin import DynamicRawIDMixin

from users.models import User, Dealer, Agent, ControlRoomUser, DealerProfile, AgentProfile, \
                            AgentLocation, SMSAuthenticationHistory, WithdrawalRequesting, \
                            BalanceHistory, TossVirtualAccount, DealerCompany, AgentSettlementAccount, \
                            get_new_agent_profile_id

from users.forms import AgentAdminAddForm, AgentAdminForm, AgentProfileAdminForm, DealerAdminAddForm, DealerAdminForm

from pcar.admin import LatLongWidget

from .filters import DealerCompanyNameInputFilter
from .utils import generate_agent_list_xlsx, generate_dealer_company_list_xlsx


class DealerProfileAdmin(DynamicRawIDMixin, admin.StackedInline):
    model = DealerProfile
    fk_name = 'user'
    extra = 1
    min_num = 1

    dynamic_raw_id_fields = [ 'company', ]


class AffilatedDealerAdmin(DynamicRawIDMixin, admin.StackedInline):
    model = DealerProfile
    extra = 0
    min_num = 0
    max_num = 0
    can_delete = False

    readonly_fields = [
        'mobile_number',
    ]

    exclude = [
        'user',
        'cooperation_level',
        'settlement_date',
    ]

    def mobile_number(self, obj):
        return obj.user.mobile_number

    mobile_number.short_description = '핸드폰 번호'


class AgentProfileAdmin(admin.StackedInline):
    form = AgentProfileAdminForm
    model = AgentProfile
    fk_name = 'user'
    extra = 1
    min_num = 1

    def get_exclude(self, request, obj=None):
        if not obj:
            return [ 'id', ]

        return self.exclude


class AgentSettlementAccountAdmin(admin.StackedInline):
    model = AgentSettlementAccount
    extra = 1

    '''
    formfield_overrides = {
        geomodels.PointField: { 'widget': LatLongWidget }
    }
    '''


class AgentLocationAdmin(admin.StackedInline):
    model = AgentLocation
    fk_name = 'agent'
    extra = 1
    min_num = 1

    readonly_fields = ( 'updated_at', )
    '''
    formfield_overrides = {
        geomodels.PointField: { 'widget': LatLongWidget }
    }
    '''

@admin.register(DealerCompany)
class DealerCompanyAdmin(admin.ModelAdmin):
    exclude = [ 'uuid', ]

    inlines = [
        AffilatedDealerAdmin,
    ]

    actions = [ 'export_as_xlsx', ]

    list_display = (
        'name', 'id', 'business_registration_number', 'representative_name', 'business_items', 'business_categories', 'require_publish_bill', \
        'get_evaluation_count_current_month', 'get_inspection_count_current_month', 'get_delivery_count_current_month', \
        'get_evaluation_costs_current_month', 'get_inspection_costs_current_month', 'get_delivery_costs_current_month', 'get_total_costs_current_month',
        'get_acc_evaluation_costs', 'get_acc_inspection_costs', 'get_acc_delivery_costs', 'get_acc_total_costs',
    )

    def export_as_xlsx(self, request, queryset):
        xlsx_output = generate_dealer_company_list_xlsx(queryset)

        filename = '고객사 목록.xlsx'
        response = HttpResponse(
            xlsx_output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(quote(filename.encode('utf-8')))

        return response

    export_as_xlsx.short_description = '선택 목록 엑셀로 출력하기'

    def business_items(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        if len(obj.dealer_profile.company.business_items) == 0:
            return '-'

        return ', '.join(obj.dealer_profile.company.business_items)

    business_items.short_description = '회사 아이템'

    def business_categories(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        if len(obj.dealer_profile.company.business_categories) == 0:
            return '-'

        return ', '.join(obj.dealer_profile.company.business_categories)

    business_categories.short_description = '사업분류'

    def get_evaluation_count_current_month(self, obj):
        return obj.evaluation_count_current_month

    get_evaluation_count_current_month.short_description = '당월 평가 횟수'

    def get_inspection_count_current_month(self, obj):
        return obj.inspection_count_current_month

    get_inspection_count_current_month.short_description = '당월 검수 횟수'

    def get_delivery_count_current_month(self, obj):
        return obj.delivery_count_current_month

    get_delivery_count_current_month.short_description = '당월 탁송 횟수'

    def get_evaluation_costs_current_month(self, obj):
        return obj.evaluation_costs_current_month

    get_evaluation_costs_current_month.short_description = '당월 평가 매출액'

    def get_inspection_costs_current_month(self, obj):
        return obj.inspection_costs_current_month

    get_inspection_costs_current_month.short_description = '당월 검수 매출액'

    def get_delivery_costs_current_month(self, obj):
        return obj.delivery_costs_current_month

    get_delivery_costs_current_month.short_description = '당월 탁송 매출액'

    def get_total_costs_current_month(self, obj):
        return obj.total_costs_current_month

    get_total_costs_current_month.short_description = '당월 총 매출액'

    def get_acc_evaluation_costs(self, obj):
        return obj.acc_evaluation_costs

    get_acc_evaluation_costs.short_description = '총 누적 평가 매출액'

    def get_acc_inspection_costs(self, obj):
        return obj.acc_inspection_costs

    get_acc_inspection_costs.short_description = '총 누적 검수 매출액'

    def get_acc_delivery_costs(self, obj):
        return obj.acc_delivery_costs

    get_acc_delivery_costs.short_description = '총 누적 탁송 매출액'

    def get_acc_total_costs(self, obj):
        return obj.acc_total_costs

    get_acc_total_costs.short_description = '총 누적 매출액'


@admin.register(Dealer)
class DealerAdmin(auth_admin.UserAdmin):
    form = DealerAdminForm
    add_form = DealerAdminAddForm

    list_per_page = 30

    inlines = [
        DealerProfileAdmin,
    ]

    fieldsets = (
        ('기본 정보', {
            'fields': (
                'mobile_number', 'name', 'username', 'password', 'is_staff', 'is_test_account', 'created_at', 'referer',
                'api_usage_type', 'api_id', 'api_secret',
            )
        }),
    )

    add_fieldsets = (
        ('기본 정보', {
            'fields': ( 'mobile_number', 'name', 'referer', )
        }),
    )

    ordering = ( '-created_at', )

    raw_id_fields = ( 'referer', )

    list_display = (
        'company_id', 'mobile_number', 'name', 'company_name', 'representative_name', 'require_publish_bill', \
        'business_registration_number', 'business_items', 'business_categories', 'get_referer', 'created_at', \
        'get_evaluation_count_current_month', 'get_inspection_count_current_month', 'get_delivery_count_current_month', \
        'get_evaluation_costs_current_month', 'get_inspection_costs_current_month', 'get_delivery_costs_current_month', 'get_total_costs_current_month',
        'get_acc_evaluation_costs', 'get_acc_inspection_costs', 'get_acc_delivery_costs', 'get_acc_total_costs',
    )

    list_filter = (
        'dealer_profile__company__require_publish_bill',
        DealerCompanyNameInputFilter,
    )

    def company_id(self, obj):
        return obj.pk

    company_id.short_description = '업체코드'

    def company_name(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        return obj.dealer_profile.company.name

    company_name.short_description = '상사 이름'

    def representative_name(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        return obj.dealer_profile.company.representative_name or '-'

    representative_name.short_description = '대표자 이름'

    def require_publish_bill(self, obj):
        if not obj.dealer_profile.company:
            return False

        return obj.dealer_profile.company.require_publish_bill

    require_publish_bill.short_description = '계산서 발행유무'
    require_publish_bill.boolean = True

    def business_registration_number(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        return obj.dealer_profile.company.business_registration_number

    business_registration_number.short_description = '사업자 등록번호'

    def business_items(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        if len(obj.dealer_profile.company.business_items) == 0:
            return '-'

        return ', '.join(obj.dealer_profile.company.business_items)

    business_items.short_description = '회사 아이템'

    def business_categories(self, obj):
        if not obj.dealer_profile.company:
            return '-'

        if len(obj.dealer_profile.company.business_categories) == 0:
            return '-'

        return ', '.join(obj.dealer_profile.company.business_categories)

    business_categories.short_description = '사업분류'

    def get_referer(self, obj):
        if not obj.referer:
            return '-'
        else:
            change_url = reverse('admin:users_agent_change', args=(obj.referer.id,))
            return mark_safe(f'<a href="{ change_url }">{ obj.referer.name }</a>')

    get_referer.short_description = '추천인'

    def get_queryset(self, request):
        qs = super(DealerAdmin, self).get_queryset(request)

        return qs.filter(Q(dealer_profile__isnull=False))

    def save_model(self, request, obj, form, change):
        is_creating = not change

        super(DealerAdmin, self).save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        is_creating = not change

        if is_creating:
            for formset in formsets:
                if formset.model == DealerProfile:
                    instances = formset.save(commit=False)

                    if len(instances) == 0:
                        DealerProfile.objects.create(user=form.instance)

        super(DealerAdmin, self).save_related(request, form, formsets, change)

    def get_evaluation_count_current_month(self, obj):
        return obj.dealer_profile.evaluation_count_current_month

    get_evaluation_count_current_month.short_description = '당월 평가 횟수'

    def get_inspection_count_current_month(self, obj):
        return obj.dealer_profile.inspection_count_current_month

    get_inspection_count_current_month.short_description = '당월 검수 횟수'

    def get_delivery_count_current_month(self, obj):
        return obj.dealer_profile.delivery_count_current_month

    get_delivery_count_current_month.short_description = '당월 탁송 횟수'

    def get_evaluation_costs_current_month(self, obj):
        return obj.dealer_profile.evaluation_costs_current_month

    get_evaluation_costs_current_month.short_description = '당월 평가 매출액'

    def get_inspection_costs_current_month(self, obj):
        return obj.dealer_profile.inspection_costs_current_month

    get_inspection_costs_current_month.short_description = '당월 검수 매출액'

    def get_delivery_costs_current_month(self, obj):
        return obj.dealer_profile.delivery_costs_current_month

    get_delivery_costs_current_month.short_description = '당월 탁송 매출액'

    def get_total_costs_current_month(self, obj):
        return obj.dealer_profile.total_costs_current_month

    get_total_costs_current_month.short_description = '당월 총 매출액'

    def get_acc_evaluation_costs(self, obj):
        return obj.dealer_profile.acc_evaluation_costs

    get_acc_evaluation_costs.short_description = '총 누적 평가 매출액'

    def get_acc_inspection_costs(self, obj):
        return obj.dealer_profile.acc_inspection_costs

    get_acc_inspection_costs.short_description = '총 누적 검수 매출액'

    def get_acc_delivery_costs(self, obj):
        return obj.dealer_profile.acc_delivery_costs

    get_acc_delivery_costs.short_description = '총 누적 탁송 매출액'

    def get_acc_total_costs(self, obj):
        return obj.dealer_profile.acc_total_costs

    get_acc_total_costs.short_description = '총 누적 매출액'


@admin.register(Agent)
class AgentAdmin(auth_admin.UserAdmin):
    form = AgentAdminForm
    add_form = AgentAdminAddForm

    list_per_page = 30

    inlines = [
        AgentProfileAdmin,
        AgentSettlementAccountAdmin,
        AgentLocationAdmin,
    ]

    actions = [ 'export_as_xlsx', ]

    fieldsets = (
        ('기본 정보', {
            'fields': ( 'username', 'password', 'mobile_number', 'name', 'is_staff', 'is_superuser', 'is_test_account', )
        }),
    )

    add_fieldsets = (
        ('기본 정보', {
            'fields': ( 'mobile_number', 'name', 'is_staff', 'is_superuser', 'is_test_account', )
        }),
    )

    ordering = ( 'agent_profile__id', )

    list_display = (
        'name', 'agent_profile_id', 'mobile_number', 'agent_birthday', 'agent_home_address', \
        'agent_settlement_account_bank', 'agent_settlement_account_number', 'agent_settlement_account_holder_name',
        'agent_affiliated_area', 'agent_level', 'activity_areas', 'is_insurance_expired', 'remaining_balance',
    )

    list_filter = ( 'agent_profile__level', 'agent_location__using_auto_dispatch', )

    search_fields = (
        'name',
        'agent_profile__id',
    )

    def export_as_xlsx(self, request, queryset):
        xlsx_output = generate_agent_list_xlsx(queryset)

        filename = '평카인 목록.xlsx'
        response = HttpResponse(
            xlsx_output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        response['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(quote(filename.encode('utf-8')))

        return response

    export_as_xlsx.short_description = '선택 목록 엑셀로 출력하기'

    def agent_profile_id(self, obj):
        return obj.agent_profile.id

    agent_profile_id.short_description = '평카인 사번'

    def agent_birthday(self, obj):
        return obj.agent_profile.birthday

    agent_birthday.short_description = '생년월일'

    def agent_home_address(self, obj):
        return obj.agent_profile.home_address

    agent_home_address.short_description = '주소'

    def agent_settlement_account_bank(self, obj):
        return obj.agent_settlement_account.account_holder or ''

    agent_settlement_account_bank.short_description = '예금주'

    def agent_settlement_account_number(self, obj):
        return obj.agent_settlement_account.account_number or ''

    agent_settlement_account_number.short_description = '계좌번호'

    def agent_settlement_account_holder_name(self, obj):
        return obj.agent_settlement_account.account_holder or ''

    agent_settlement_account_holder_name.short_description = '예금주'

    def agent_affiliated_area(self, obj):
        return obj.agent_profile.affiliated_area

    agent_affiliated_area.short_description = '소속 지역'

    def agent_level(self, obj):
        return obj.agent_profile.level

    agent_level.short_description = '평카인 레벨'

    def activity_areas(self, obj):
        if len(obj.agent_profile.activity_areas) == 0:
            return '-'

        return ', '.join(obj.agent_profile.activity_areas)

    activity_areas.short_description = '활동영역'

    def is_insurance_expired(self, obj):
        if obj.agent_profile.insurance_expiry_date is None:
            return True

        return obj.agent_profile.insurance_expiry_date > timezone.now().date()

    is_insurance_expired.boolean = True
    is_insurance_expired.short_description = '보험 유효 여부 (X 일 경우 만료)'

    def remaining_balance(self, obj):
        return f'{obj.agent_profile.balance:,}원'

    remaining_balance.short_description = '현 적립금'

    def get_queryset(self, request):
        qs = super(AgentAdmin, self).get_queryset(request)

        return qs.filter(Q(agent_profile__isnull=False))

    def save_model(self, request, obj, form, change):
        super(AgentAdmin, self).save_model(request, obj, form, change)

        if not change:
            AgentLocation.objects.create(agent=obj)


@admin.register(ControlRoomUser)
class ControlRoomUserAdmin(auth_admin.UserAdmin):
    fieldsets = (
        ('기본 정보', {
            'fields': ('mobile_number', 'password', 'name', 'is_superuser', )
        }),
    )

    ordering = ( 'mobile_number', )

    list_display = (
        'mobile_number', 'name',
    )

    search_fields = (
        'name',
        'mobile_number',
    )

    list_filter = ()

    def get_queryset(self, request):
        qs = super(ControlRoomUserAdmin, self).get_queryset(request)

        return qs.filter(Q(is_superuser=True))

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(SMSAuthenticationHistory)
class SMSAuthenticationHistoryAdmin(admin.ModelAdmin):
    list_display = ( 'mobile_number', 'authentication_code', 'created_at', )
    list_per_page = 30


@admin.register(BalanceHistory)
class BalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ( 'id', 'transaction_at', 'type', 'amount', )

    raw_id_fields = ( 'user', )


@admin.register(WithdrawalRequesting)
class WithdrawalRequestingAdmin(admin.ModelAdmin):
    list_display = ( 'agent', 'requested_at', 'amount', 'is_processed', )
    list_filter = ( 'is_processed', )

    actions = [ 'processing_withdrawal', ]

    def processing_withdrawal(self, request, queryset):
        for withdrawal_requesting in list(queryset.filter(is_processed=False)):
            withdrawal_requesting.is_processed = True
            withdrawal_requesting.save()

            BalanceHistory.objects.create(
                user=withdrawal_requesting.agent,
                type='withdrawal',
                amount=withdrawal_requesting.amount,
            )

    processing_withdrawal.short_description = '선택된 내역을 모두 입금 처리합니다'


@admin.register(TossVirtualAccount)
class TossVirtualAccountAdmin(admin.ModelAdmin):
    pass
