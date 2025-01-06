from django.db import models
from django.contrib.gis.db import models as gis_models

from pcar.helpers import PreprocessUploadPath

from users.models import Agent


class AgentLocation(models.Model):
    agent = models.OneToOneField(
        Agent,
        on_delete=models.CASCADE,
        related_name='agent_location',
        verbose_name='대상 평카인',
    )

    updated_at = models.DateTimeField(
        verbose_name='마지막 업데이트 시각',
        auto_now_add=True,
    )

    is_end_of_work = models.BooleanField(
        verbose_name='업무 종료 여부',
        default=False,
    )

    coord = gis_models.PointField(
        null=True,
        blank=True,
        verbose_name='현재 평카인 좌표',
    )

    manual_road_address = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name='수동 도로명 주소',
    )

    manual_coord = gis_models.PointField(
        null=True,
        blank=True,
        verbose_name='수동 주소 좌표',
    )

    using_auto_dispatch = models.BooleanField(
        default=True,
        verbose_name='자동배차 사용유무',
    )

    desired_destination_address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='희망 도착지',
    )

    using_manual_address = models.BooleanField(
        default=False,
        verbose_name='수동 주소로 검색 여부',
    )

    class Meta:
        db_table = 'agent_locations'
        verbose_name = '에이전트 위치정보'
        verbose_name_plural = '에이전트 위치정보 목록'
