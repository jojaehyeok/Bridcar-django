import random
import string

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.db.models.aggregates import Sum
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from django_random_id_model import RandomIDModel

from phonenumber_field.modelfields import PhoneNumberField

from users.constants import API_USAGE_TYPES


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, *args, **kwargs):
        user = self.model(
            username=username,
            **kwargs,
        )

        #user.set_password(password)
        user.set_unusable_password()
        user.save(using=self._db)

        return user

    def create_superuser(self, username, password, *args, **kwargs):
        user = self.create_user(
            username=username,
            name='최고관리자',
            is_staff=True,
            is_superuser=True,
            **kwargs,
        )

        user.set_password(password)
        user.save(using=self._db)

        from .agent_profile import AgentProfile
        from .agent_location import AgentLocation

        last_agent_profile_id = 1

        try:
            last_agent_profile_id = (AgentProfile.objects.latest('-id').id) + 1
        except AgentProfile.DoesNotExist:
            pass

        AgentProfile.objects.create(
            id=last_agent_profile_id,
            user=user,
        )

        AgentLocation.objects.create(agent=user)

        return user


class User(RandomIDModel, AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    username = models.CharField(
        max_length=32,
        verbose_name='유저네임 (필요시 직접 수정)',
        unique=True,
        blank=True,
    )

    name = models.CharField(
        max_length=32,
        verbose_name='회원 이름 (실명)',
    )

    mobile_number = PhoneNumberField(
        verbose_name='핸드폰 번호',
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(
        default=False,
        verbose_name='관리자 페이지 접근 가능 권한',
    )

    is_superuser = models.BooleanField(
        default=False,
        verbose_name='최고관리자 (상황실 웹사이트 접근 가능)',
    )

    is_test_account = models.BooleanField(
        default=False,
        verbose_name='테스트용 계정 (애플 심사 등)'
    )

    api_id = models.CharField(
        max_length=32,
        verbose_name='API ID',
        null=True,
        blank=True,
    )

    api_usage_type = models.CharField(
        max_length=16,
        verbose_name='API 사용 구분',
        choices=API_USAGE_TYPES,
        null=True,
        blank=True,
    )

    api_secret = models.CharField(
        max_length=32,
        verbose_name='API Secret',
        null=True,
        blank=True,
    )

    referer = models.ForeignKey(
        'Agent',
        on_delete=models.CASCADE,
        related_name='brought_users',
        verbose_name='추천인',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name='가입 일자',
    )

    USERNAME_FIELD = 'username'

    class Meta:
        db_table = 'users'
        verbose_name = '유저'
        verbose_name_plural = '유저 목록'

    def save(self, *args, **kwargs):
        is_creating = not self.pk

        if is_creating:
            if not self.username:
                username = ''

                while True:
                    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))

                    try:
                        User.objects.get(username=username)
                    except:
                        break

                self.username = username

            if self.created_at == None:
                self.created_at = timezone.now()

        return super(User, self).save(*args, **kwargs)

    def __unicode__(self):
        return f'{ self.name }'

    def __str__(self):
        return f'{ self.name }'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def check_authentication_code(self, authentication_code, purpose='signin'):
        from .sms_authentication_history import SMSAuthenticationHistory

        now = timezone.now()

        return SMSAuthenticationHistory.objects.filter(
            mobile_number=self.mobile_number,
            purpose=purpose,
            created_at__gte=now - timezone.timedelta(minutes=5),
            authentication_code=authentication_code,
        ).first() != None

    @property
    def is_agent(self):
        return hasattr(self, 'agent_profile')

    @property
    def is_dealer(self):
        return hasattr(self, 'dealer_profile')

    @property
    def processing_virtual_account(self):
        now = timezone.now()

        return self.toss_virtual_accounts.filter(
            Q(expired_at__gte=now)& \
            Q(is_deposited=False)
        ) \
        .first()


class DealerManager(models.Manager):
    def get_queryset(self):
        return super(DealerManager, self) \
            .get_queryset() \
            .filter(dealer_profile__isnull=False)


class Dealer(User):
    objects = DealerManager()

    class Meta:
        proxy = True
        verbose_name = '딜러'
        verbose_name_plural = '딜러 목록'


class AgentManager(models.Manager):
    def get_queryset(self):
        return super(AgentManager, self) \
            .get_queryset() \
            .filter(agent_profile__isnull=False)


class Agent(User):
    objects = AgentManager()

    class Meta:
        proxy = True
        verbose_name = '평카인'
        verbose_name_plural = '평카인 목록'

    @property
    def currently_working_requesting(self):
        from requestings.models import RequestingHistory

        return RequestingHistory.objects \
            .filter(
                Q(agent=self)& \
                (
                    ~Q(status='DONE')& \
                    ~Q(status='CANCELLED')
                )
            ) \
            .first()

    @property
    def avg_3month_withdrawal_amount(self):
        from .withdrawal_requesting import WithdrawalRequesting

        now = timezone.now()

        result = WithdrawalRequesting.objects \
            .filter(
                Q(agent=self)& \
                Q(is_processed=True)& \
                Q(requested_at=(now - timezone.timedelta(days=90)))
            ) \
            .aggregate(amount_sum=Sum('amount'))

        return (result['amount_sum'] or 0) / 3

    @property
    def evaluation_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(user=self)& \
                Q(requesting_history__type='EVALUATION_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3

    @property
    def inspection_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(user=self)& \
                Q(requesting_history__type='INSPECTION_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3

    @property
    def delivery_count_avg_3_month(self):
        from requestings.models import RequestingSettlement

        now = timezone.now()

        return RequestingSettlement.objects \
            .filter(
                Q(user=self)& \
                Q(requesting_history__type='ONLY_DELIVERY')& \
                Q(requesting_end_at__gte=(now - timezone.timedelta(days=90)))
            ) \
            .count() / 3


class ControlRoomUser(User):
    class Meta:
        proxy = True
        verbose_name = '상황실 관리자'
        verbose_name_plural = '상황실 관리자 목록'
