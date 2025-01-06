import requests

from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos.geometry import GEOSGeometry

from phonenumber_field.modelfields import PhoneNumberField

from locations.utils import search_road_address_from_kakao


class CommonLocation(models.Model):
    coord = gis_models.PointField(
        null=True,
        blank=True,
        verbose_name='주소 좌표',
    )

    road_address = models.CharField(
        max_length=300,
        verbose_name='도로명 주소',
    )

    detail_address = models.CharField(
        max_length=300,
        default='',
        verbose_name='상세 주소'
    )

    contact = PhoneNumberField(
        verbose_name='연락처',
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'locations'
        verbose_name = '주소 정보'
        verbose_name_plural = '주소 정보 목록'

    def __str__(self):
        return self.road_address

    def save(self, need_fetch_coordinate=False, *args, **kwargs):
        if not self.pk or need_fetch_coordinate == True:
            address_search_result = search_road_address_from_kakao(self.road_address)
            lng, lat = float(address_search_result['x']), float(address_search_result['y'])

            self.coord = GEOSGeometry(f'POINT({ lng } { lat })', srid=4326)

        super(CommonLocation, self).save(*args, **kwargs)
