import sys

import pandas as pd

from requestings.models import DeliveryRegionDivision, DeliveryFeeRelation


def run():
    file_name = '/home/api-server/files/delivery_fee_table.xlsx'

    df = pd.read_excel(file_name, sheet_name='브릿카 탁송요금표')
    print('Load delivery table failed!')

    row_cities = []
    missing_cities_in_db = []
    city_model_objects = []

    try:
        for row in df.loc[4][3:]:
            row_cities.append(row)
    except:
        pass

    city_in_db_count = 0

    # 지역이 DB에 제대로 들어 있는지 체크
    for city in row_cities:
        try:
            city_model_objects.append(
                DeliveryRegionDivision.objects.get(name=city)
            )

            city_in_db_count += 1
        except:
            missing_cities_in_db.append(city)

    print(f'DB상 지역 갯수 체크: { city_in_db_count }/{ len(row_cities) }')
    print(f'DB상 누락된 지역: { str(missing_cities_in_db) }')

    is_confirmed = input('엑셀상 탁송 요금을 입력 할까요? (y/n)')

    if not is_confirmed:
        return

    for column_index, xlsx_column_index in enumerate(range(5, sys.maxsize ** 10)):
        try:
            city = ''

            for index, row_value in enumerate(df.loc[xlsx_column_index][2:]):
                if index == 0:
                    city = row_value
                else:
                    if column_index >= index:
                        continue

                    from_city = row_cities[index - 1]
                    to_city = row_cities[xlsx_column_index - 5]

                    if '제주시' in from_city or '제주시' in to_city:
                        continue

                    from_city_object = city_model_objects[index - 1]
                    to_city_object = city_model_objects[xlsx_column_index - 5]

                    # input(f'{ row_cities[index - 1] } - { row_cities[xlsx_column_index - 5] } -> { row_value }')

                    DeliveryFeeRelation.objects.create(
                        departure_region_division=from_city_object,
                        arrival_region_division=to_city_object,
                        delivery_fee=(int(row_value) * 1000),
                    )
        except Exception as e:
            print(e)
            break

        print(f'{ column_index }번 칼럼 입력 완료\n')

