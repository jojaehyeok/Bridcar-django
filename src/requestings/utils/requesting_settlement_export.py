import io

import xlsxwriter

from pytz import timezone

from requestings.constants import REQUESTING_TYPES


def generate_requesting_settlement_xlsx(queryset, custom_title='', for_agent=False):
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output)

    workbook.formats[0].set_font_size(11)
    workbook.formats[0].set_font_name('맑은 고딕')

    worksheet = workbook.add_worksheet()

    worksheet.set_column(1, 1, 13) # 의뢰번호 너비
    worksheet.set_column(2, 2, 10) # 의뢰구분 너비
    worksheet.set_column(3, 3, 25) # 의뢰구분 너비
    worksheet.set_column(4, 4, 25) # 의뢰구분 너비
    worksheet.set_column(5, 5, 30) # 출발지 너비
    worksheet.set_column(6, 6, 30) # 도착지 너비

    #company_ids = list(set(queryset.values_list('requesting_history__client__dealer_profile__company__id', flat=True)))

    company_exists_settlements = queryset \
        .filter(requesting_history__client__dealer_profile__company__isnull=False) \
        .order_by('requesting_history__client__dealer_profile__company__id') \
        .only('requesting_history__client__dealer_profile__company__id') \
        .distinct('requesting_history__client__dealer_profile__company__id')

    if custom_title == '':
        if len(company_exists_settlements) == 1:
            title = f'{ queryset[0].requesting_history.client.dealer_profile.company.name } 정산목록'
        else:
            title = '정산목록'
    else:
        title = custom_title

    merge_format = workbook.add_format({
        'font_size': 22,
        'font_name': '맑은 고딕',
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#ffff00',
    })

    account_information_format = workbook.add_format({
        'font_size': 18,
        'font_name': '맑은 고딕',
        'font_color': 'white',
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#808080',
    })

    th_bold_format = workbook.add_format({
        'bold': 1,
    })

    th_yellow_bold_format = workbook.add_format({
        'bold': 1,
        'bg_color': '#ffff00',
    })

    cost_summary_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })

    cost_summary_value_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0'
    })

    fuel_cost_summary_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#eeece1',
    })

    fuel_cost_summary_value_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0',
        'bg_color': '#eeece1',
    })

    additional_cost_summary_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#f2f2f2',
    })

    additional_cost_summary_value_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0',
        'bg_color': '#f2f2f2',
    })

    total_cost_summary_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#bfbfbf',
    })

    total_cost_summary_value_format = workbook.add_format({
        'font_name': '맑은 고딕',
        'font_size': 14,
        'bold': 1,
        'border': 1,
        'align': 'right',
        'valign': 'vcenter',
        'num_format': '#,##0',
        'bg_color': '#bfbfbf',
    })

    num_fmt = workbook.add_format({ 'num_format': '#,##0' })

    worksheet.merge_range('E3:Q4', title, merge_format)

    start_row_num = 6

    worksheet.write(start_row_num, 0, '정산번호', th_bold_format)
    worksheet.write(start_row_num, 1, '의뢰번호', th_bold_format)
    worksheet.write(start_row_num, 2, '의뢰구분', th_bold_format)
    worksheet.write(start_row_num, 3, '의뢰 접수 일시', th_bold_format)
    worksheet.write(start_row_num, 4, '의뢰 완료 일자', th_bold_format)
    worksheet.write(start_row_num, 5, '출발지', th_bold_format)
    worksheet.write(start_row_num, 6, '도착지', th_bold_format)
    worksheet.write(start_row_num, 7, '차종', th_yellow_bold_format)
    worksheet.write(start_row_num, 8, '차량번호', th_yellow_bold_format)
    worksheet.write(start_row_num, 9, '평가비', th_bold_format)
    worksheet.write(start_row_num, 10, '검수비', th_bold_format)
    worksheet.write(start_row_num, 11, '탁송비', th_bold_format)
    worksheet.write(start_row_num, 12, '추가 제안 요금', th_bold_format)
    worksheet.write(start_row_num, 13, '소계 (공급가액)', th_bold_format)
    worksheet.write(start_row_num, 14, 'VAT', th_bold_format)
    worksheet.write(start_row_num, 15, '합계금액', th_bold_format)
    worksheet.write(start_row_num, 16, '주유비', th_yellow_bold_format)
    worksheet.write(start_row_num, 17, '기타 비용 합계', th_bold_format)
    worksheet.write(start_row_num, 18, '기타 비용 내역', th_yellow_bold_format)
    worksheet.write(start_row_num, 19, '청구 금액', th_bold_format)
    worksheet.write(start_row_num, 20, '결제구분', th_yellow_bold_format)

    evaluation_cost_sum = 0
    inspection_cost_sum = 0
    delivering_cost_sum = 0
    additional_suggested_cost_sum = 0
    direct_costs_sum = 0
    fuel_costs_sum = 0
    vat_sum = 0
    direct_costs_sum_with_vat_sum = 0
    additional_costs_sum = 0
    total_cost_sum = 0

    for settlement in queryset:
        start_row_num += 1

        evaluation_cost_sum += settlement.evaluation_cost
        inspection_cost_sum += settlement.inspection_cost
        delivering_cost_sum += settlement.delivering_cost
        additional_suggested_cost_sum += settlement.additional_suggested_cost
        direct_costs_sum += settlement.direct_costs
        vat_sum += settlement.vat
        direct_costs_sum_with_vat_sum += (settlement.direct_costs + settlement.vat)
        fuel_costs_sum += settlement.fuel_costs
        additional_costs_sum += settlement.total_additional_cost
        total_cost_sum += settlement.total_cost

        worksheet.write(start_row_num, 0, str(settlement.pk))
        worksheet.write(start_row_num, 1, str(settlement.requesting_history.pk))
        worksheet.write(start_row_num, 2, dict(REQUESTING_TYPES)[settlement.requesting_history.type])

        worksheet.write(
            start_row_num,
            3,
            settlement.requesting_history.created_at.astimezone(timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일 %H시 %M분')
        )

        worksheet.write(
            start_row_num,
            4,
            settlement.requesting_end_at.astimezone(timezone('Asia/Seoul')).strftime('%Y년 %m월 %d일 %H시 %M분')
        )

        worksheet.write(
            start_row_num,
            5,
            f'{ settlement.requesting_history.source_location.road_address } { settlement.requesting_history.source_location.detail_address }'
        )

        worksheet.write(
            start_row_num,
            6,
            f'{ settlement.requesting_history.destination_location.road_address } { settlement.requesting_history.destination_location.detail_address }'
        )

        # 차종
        worksheet.write(
            start_row_num,
            7,
            settlement.requesting_history.car.type,
        )

        # 차량번호
        worksheet.write(
            start_row_num,
            8,
            settlement.requesting_history.car.number,
        )

        # 평가비
        worksheet.write(
            start_row_num,
            9,
            settlement.evaluation_cost or 0,
            num_fmt,
        )

        # 검수비
        worksheet.write(
            start_row_num,
            10,
            settlement.inspection_cost or 0,
            num_fmt,
        )

        # 탁송비
        worksheet.write(
            start_row_num,
            11,
            settlement.delivering_cost or 0,
            num_fmt,
        )

        # 추가 제안 요금
        worksheet.write(
            start_row_num,
            12,
            settlement.additional_suggested_cost,
            num_fmt,
        )

        # 소계
        worksheet.write(
            start_row_num,
            13,
            settlement.direct_costs,
            num_fmt,
        )

        # VAT
        worksheet.write(
            start_row_num,
            14,
            settlement.vat,
            num_fmt,
        )

        # 합계 금액
        worksheet.write(
            start_row_num,
            15,
            settlement.direct_costs + settlement.vat,
            num_fmt,
        )

        # 주유
        worksheet.write(
            start_row_num,
            16,
            settlement.fuel_costs,
            num_fmt,
        )

        # 기타 비용 합계
        worksheet.write(
            start_row_num,
            17,
            settlement.total_additional_cost,
            num_fmt,
        )

        # 기타 비용 내역
        worksheet.write(
            start_row_num,
            18,
            settlement.additional_costs_summary,
            num_fmt,
        )

        # 기타 비용 합계
        worksheet.write(
            start_row_num,
            19,
            settlement.total_cost,
            num_fmt,
        )

        # 결제 구분
        worksheet.write(
            start_row_num,
            20,
            '현금' if settlement.is_onsite_payment == True else '후불',
            num_fmt,
        )

    start_row_num += 1

    worksheet.write(start_row_num, 8, '계')
    worksheet.write(start_row_num, 9, evaluation_cost_sum, num_fmt)
    worksheet.write(start_row_num, 10, inspection_cost_sum, num_fmt)
    worksheet.write(start_row_num, 11, delivering_cost_sum, num_fmt)
    worksheet.write(start_row_num, 12, additional_suggested_cost_sum, num_fmt)
    worksheet.write(start_row_num, 13, direct_costs_sum, num_fmt)
    worksheet.write(start_row_num, 14, vat_sum, num_fmt)
    worksheet.write(start_row_num, 15, direct_costs_sum_with_vat_sum, num_fmt)
    worksheet.write(start_row_num, 16, fuel_costs_sum, num_fmt)
    worksheet.write(start_row_num, 17, additional_costs_sum, num_fmt)
    worksheet.write(start_row_num, 19, total_cost_sum, num_fmt)

    start_row_num += 4

    worksheet.set_row(start_row_num - 1, 20)
    worksheet.set_row(start_row_num, 20)
    worksheet.set_row(start_row_num + 1, 20)
    worksheet.set_row(start_row_num + 2, 20)
    worksheet.set_row(start_row_num + 3, 20)
    worksheet.set_row(start_row_num + 4, 20)

    if not for_agent:
        worksheet.merge_range(f'B{ start_row_num }:D{ start_row_num }', '탁송비계', cost_summary_format)
        worksheet.write(start_row_num - 1, 4, delivering_cost_sum, cost_summary_value_format)

        start_row_num += 1

        worksheet.merge_range(f'B{ start_row_num }:D{ start_row_num }', '부가세', cost_summary_format)
        worksheet.write(start_row_num - 1, 4, vat_sum, cost_summary_value_format)

        start_row_num += 1

        worksheet.merge_range(f'B{ start_row_num }:D{ start_row_num }', '세금계산서발행금액', cost_summary_format)
        worksheet.write(start_row_num - 1, 4, direct_costs_sum_with_vat_sum, cost_summary_value_format)

        start_row_num += 1

        worksheet.merge_range(f'B{ start_row_num }:D{ start_row_num }', '주유비', fuel_cost_summary_format)
        worksheet.write(start_row_num - 1, 4, fuel_costs_sum, fuel_cost_summary_value_format)

        start_row_num += 1

        worksheet.merge_range(f'B{ start_row_num }:D{ start_row_num }', '기  타', additional_cost_summary_format)
        worksheet.write(start_row_num - 1, 4, additional_costs_sum, additional_cost_summary_value_format)

        start_row_num += 1

        worksheet.merge_range(f'B{ start_row_num }:D{ start_row_num }', '총 결제 금액', total_cost_summary_format)
        worksheet.write(start_row_num - 1, 4, total_cost_sum, total_cost_summary_value_format)

        start_row_num += 3

        worksheet.merge_range(f'B{ start_row_num }:G{ start_row_num }', '입금은행 : 하나은행', account_information_format)
        worksheet.merge_range(f'B{ start_row_num + 1 }:G{ start_row_num + 1 }', '계좌번호 : 1111-1111111-1111', account_information_format)
        worksheet.merge_range(f'B{ start_row_num + 2 }:G{ start_row_num + 2 }', '예금주 : 주식회사 브릿카', account_information_format)

        worksheet.set_row(start_row_num - 1, 30)
        worksheet.set_row(start_row_num, 30)
        worksheet.set_row(start_row_num + 1, 30)

    workbook.close()

    output.seek(0)

    return output
