from django.db import models
from django.db.models import Q
from django.db.models.functions import Length
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator

from multiselectfield import MultiSelectField

from pcar.helpers import PreprocessUploadPath

from users.constants import AGENT_LEVEL, AGENT_ACTIVITY_AREAS, AGENT_REVIEW_LEVEL, AGENT_TEST_RESULTS

from .user import Agent


def profile_image_image_path_getter(instance):
    return f'users/{ instance.user.id }'


def get_new_agent_profile_id():
    new_agent_id = ''

    try:
        last_agent = Agent.objects \
            .annotate(profile_id_length=Length('agent_profile__id')) \
            .filter(
                Q(agent_profile__id__startswith='P')& \
                Q(profile_id_length=9)
            ) \
            .latest('created_at')

        id_number = int(last_agent.agent_profile.id.split('P')[1])
        id_number += 1

        new_agent_id = 'P' + str(id_number).zfill(8)
    except Agent.DoesNotExist:
        new_agent_id = 'P00000100'

    return new_agent_id


class AgentProfile(models.Model):
    id = models.CharField(
        max_length=32,
        primary_key=True,
        verbose_name='평카인 사번',
    )

    user = models.OneToOneField(
        Agent,
        on_delete=models.CASCADE,
        related_name='agent_profile',
        verbose_name='회원이름',
    )

    level = models.CharField(
        max_length=10,
        default='A',
        choices=AGENT_LEVEL,
        verbose_name='평카인 레벨',
    )

    profile_image = models.ImageField(
        upload_to=PreprocessUploadPath(
            profile_image_image_path_getter,
            filename_prefix='agent_profile_image',
            use_uuid_name=True,
        ),
        default='/default-user-image.jpg',
        null=True,
        blank=True,
        verbose_name='평카인 프로필 사진',
    )

    referer_revenue_rate = models.FloatField(
        validators=[
            MaxValueValidator(30),
            MinValueValidator(1),
        ],
        verbose_name='홍보 수익금률 (%)',
        default=5,
    )

    birthday = models.DateField(
        null=True,
        blank=True,
        verbose_name='생년월일',
    )

    home_address = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name='주소',
    )

    training_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='평카인 교육 시작일',
    )

    training_completion_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='평카인 교육 수료일',
    )

    first_working_start_date = models.DateField(
        verbose_name='최초 근무 시작일',
        null=True,
        blank=True,
    )

    monthly_insurance_cost = models.PositiveIntegerField(
        default=0,
        verbose_name='월 보험금',
    )

    insurance_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text='보험 만료 시 해당 평카인은 오더에 배차가 불가능합니다',
        verbose_name='보험 만료 일시',
    )

    evaluation_certification = models.ImageField(
        upload_to=PreprocessUploadPath(
            profile_image_image_path_getter,
            filename_prefix='agent_evaluation_certification',
            use_uuid_name=True,
        ),
        null=True,
        blank=True,
        verbose_name='진단평가사 자격증',
    )

    career = models.TextField(
        null=True,
        blank=True,
        verbose_name='경력내용',
    )

    affiliated_area = models.CharField(
        max_length=128,
        verbose_name='소속지역',
        null=True,
        blank=True,
    )

    activity_areas = MultiSelectField(
        max_length=128,
        choices=AGENT_ACTIVITY_AREAS,
        verbose_name='활동 현황',
        null=True,
        blank=True,
    )

    balance = models.PositiveIntegerField(
        default=0,
        verbose_name='현재 잔액',
    )

    first_working_area = models.CharField(
        max_length=256,
        verbose_name='최초 근무지역',
        null=True,
        blank=True,
    )

    current_working_area = models.CharField(
        max_length=256,
        verbose_name='현근무지',
        null=True,
        blank=True,
    )

    closed_days = models.CharField(
        max_length=256,
        verbose_name='휴무요일',
        null=True,
        blank=True,
    )

    weekend_charge_working_area = models.CharField(
        max_length=256,
        verbose_name='현 주말 전담반 근무지역',
        null=True,
        blank=True,
    )

    total_evaluation_count = models.PositiveIntegerField(
        verbose_name='총 평가 횟수',
        default=0,
    )

    total_inspection_count = models.PositiveIntegerField(
        verbose_name='총 검수 횟수',
        default=0,
    )

    total_delivery_count = models.PositiveIntegerField(
        verbose_name='총 탁송 횟수',
        default=0,
    )

    total_marketing_count = models.PositiveIntegerField(
        verbose_name='총 홍보 횟수',
        default=0,
    )

    evaluation_score = models.CharField(
        max_length=32,
        choices=AGENT_REVIEW_LEVEL,
        null=True,
        blank=True,
        verbose_name='평가 레벨'
    )

    inspection_score = models.CharField(
        max_length=32,
        choices=AGENT_REVIEW_LEVEL,
        null=True,
        blank=True,
        verbose_name='검수 레벨'
    )

    delivery_score = models.CharField(
        max_length=32,
        choices=AGENT_REVIEW_LEVEL,
        null=True,
        blank=True,
        verbose_name='탁송 레벨'
    )

    cs_score = models.CharField(
        max_length=32,
        choices=AGENT_REVIEW_LEVEL,
        null=True,
        blank=True,
        verbose_name='CS 레벨'
    )

    appointment_time_score = models.CharField(
        max_length=32,
        choices=AGENT_REVIEW_LEVEL,
        null=True,
        blank=True,
        verbose_name='시간 준수수준'
    )

    dotori_status = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='도토리 현황'
    )

    tendency = models.CharField(
        max_length=128,
        verbose_name='성향',
        null=True,
        blank=True,
    )

    intimacy = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='이웃친밀도',
    )

    education_participation = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='교육참여도',
    )

    ability_to_acquire_education = models.CharField(
        max_length=32,
        choices=AGENT_REVIEW_LEVEL,
        null=True,
        blank=True,
        verbose_name='교육습득능력',
    )

    supplementary_education_count = models.PositiveIntegerField(
        verbose_name='보수교육 (회)',
        null=True,
        blank=True,
    )

    collective_education_count = models.PositiveIntegerField(
        verbose_name='집체교육 (회)',
        null=True,
        blank=True,
    )

    education_grade = models.CharField(
        max_length=64,
        choices=AGENT_LEVEL,
        verbose_name='교육등급',
        null=True,
        blank=True,
    )

    completion_test_result = models.CharField(
        verbose_name='수료 테스트 결과',
        choices=AGENT_TEST_RESULTS,
        max_length=32,
        null=True,
        blank=True,
    )

    introduction = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='인사말',
    )

    class Meta:
        db_table = 'agent_profiles'
        verbose_name = '에이전트 프로필'
        verbose_name_plural = '에이전트 프로필 목록'

    def __str__(self):
        return f'사번: { self.id }'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = get_new_agent_profile_id()

        return super(AgentProfile, self).save(*args, **kwargs)


class AgentSettlementAccount(models.Model):
    user = models.OneToOneField(
        Agent,
        on_delete=models.CASCADE,
        related_name='agent_settlement_account',
    )

    bank_name = models.CharField(
        max_length=100,
        verbose_name='은행',
    )

    account_number = models.CharField(
        max_length=100,
        verbose_name='계좌번호',
    )

    account_holder = models.CharField(
        max_length=100,
        verbose_name='예금주',
    )

    class Meta:
        db_table = 'agent_settlement_accounts'
        verbose_name = '평카인 정산계좌'
        verbose_name_plural = '평카인 정산계좌 목록'
