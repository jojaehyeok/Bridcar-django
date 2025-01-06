import math
import requests

from typing import TypedDict

from django.db import models
from django.conf import settings

from rest_framework.exceptions import ParseError

class Coord(TypedDict):
    latitude: float
    longitude: float


class KakaoAddressType(TypedDict):
    region_1depth_name: str # 시도
    region_2depth_name: str # 구
    region_3depth_name: str # 법정동
    region_3depth_h_name: str # 행정동


class SearchRoadAddressResultFromKakaoType(TypedDict):
    x: str
    y: str
    address: KakaoAddressType


def pointFieldToCoord(coord):
    if coord == None:
        return None

    lng, lat = coord

    return {
        'latitude': lat,
        'longitude': lng,
    }

def distance_to_decimal_degrees(distance, latitude):
    lat_radians = latitude * (math.pi / 180)
    result = distance.m / (111_319.5 * math.cos(lat_radians))

    return result

def search_road_address_from_kakao(road_address: str | models.CharField) -> SearchRoadAddressResultFromKakaoType:
    url = f'https://dapi.kakao.com/v2/local/search/address.json?query={ road_address }'
    headers = { 'Authorization': f'KakaoAK { settings.KAKAO_API_KEY }', }

    result = requests.get(url, headers=headers).json()

    try:
        first_search_result = result['documents'][0]
        return first_search_result
    except:
        raise ParseError('INVALID_ADDRESS')


def get_driving_distance_with_kakao(source: Coord, destination: Coord) -> float:
    url = f'https://apis-navi.kakaomobility.com/v1/directions'
    headers = { 'Authorization': f'KakaoAK { settings.KAKAO_API_KEY }', }

    result = requests.get(
        url,
        params={
            'origin': f'{ source["longitude"] },{ source["latitude"] }',
            'destination': f'{ destination["longitude"] },{ destination["latitude"] }',
        },
        headers=headers,
    ).json()

    try:
        return round(result['routes'][0]['sections'][0]['distance'] / 1000, 1)
    except:
        return 0
