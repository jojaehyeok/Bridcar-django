import io
import json
import base64
import requests

import xlsxwriter

from django.conf import settings


def generate_dealer_company_list_xlsx(queryset):
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output)

    workbook.formats[0].set_font_size(11)
    workbook.formats[0].set_font_name('맑은 고딕')

    worksheet = workbook.add_worksheet()

    for i in range(1, 34):
        if i == 1:
            worksheet.set_column(i, i, 24)

        worksheet.set_column(i, i, 15)

    basic_merge_format = workbook.add_format({
        'bg_color': '#DBEEF4',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    basic_th_bold_format = workbook.add_format({
        'bold': 1,
        'bg_color': '#DBEEF4',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    current_month_counts_merge_format = workbook.add_format({
        'bg_color': '#F2DCDB',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    current_month_counts_th_bold_format = workbook.add_format({
        'bold': 1,
        'bg_color': '#F2DCDB',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    avg_3_month_counts_merge_format = workbook.add_format({
        'bg_color': '#DBEEF4',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    avg_3_month_counts_th_format = workbook.add_format({
        'bold': True,
        'bg_color': '#DBEEF4',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    current_month_costs_th_bold_format = workbook.add_format({
        'bold': 1,
        'bg_color': '',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    center_data = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    num_fmt = workbook.add_format({ 'num_format': '#,##0' })

    start_row_num = 3

    worksheet.merge_range('A4:N4', '고객기본 정보', basic_merge_format)
    worksheet.merge_range('O4:R4', '당월 건수', current_month_counts_merge_format)
    worksheet.merge_range('S4:V4', '월 평균건수 (최근 3개월)', avg_3_month_counts_merge_format)
    worksheet.merge_range('W4:Z4', '당월매출액', current_month_counts_merge_format)
    worksheet.merge_range('AA4:AD4', '월 평균 매출액 (최근 3개월)', avg_3_month_counts_merge_format)
    worksheet.merge_range('AE4:AH4', '총 누적 매출액', current_month_counts_merge_format)

    worksheet.write(start_row_num + 1, 0, '순번', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 1, '고객(협력사) 코드번호', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 2, '고객(협력사) 분류', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 3, '상호명(법인명)', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 4, '거래개설일자', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 5, '사업자등록번호', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 6, '이메일 주소', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 7, '주소', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 8, '대표자명', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 9, '대표자 연락처', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 10, '대표번호', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 11, '담당자 명', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 12, '담당자 직위', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 13, '담당자 연락처', basic_th_bold_format)

    worksheet.write(start_row_num + 1, 14, '평가', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 15, '검수', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 16, '탁송', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 17, '총건수', current_month_counts_th_bold_format)

    worksheet.write(start_row_num + 1, 18, '평가', avg_3_month_counts_th_format)
    worksheet.write(start_row_num + 1, 19, '검수', avg_3_month_counts_th_format)
    worksheet.write(start_row_num + 1, 20, '탁송', avg_3_month_counts_th_format)
    worksheet.write(start_row_num + 1, 21, '총건수', avg_3_month_counts_th_format)

    worksheet.write(start_row_num + 1, 22, '평가', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 23, '검수', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 24, '탁송', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 25, '총건수', current_month_counts_th_bold_format)

    worksheet.write(start_row_num + 1, 26, '평가', avg_3_month_counts_th_format)
    worksheet.write(start_row_num + 1, 27, '검수', avg_3_month_counts_th_format)
    worksheet.write(start_row_num + 1, 28, '탁송', avg_3_month_counts_th_format)
    worksheet.write(start_row_num + 1, 29, '총건수', avg_3_month_counts_th_format)

    worksheet.write(start_row_num + 1, 30, '평가', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 31, '검수', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 32, '탁송', current_month_counts_th_bold_format)
    worksheet.write(start_row_num + 1, 33, '총건수', current_month_counts_th_bold_format)

    start_row_num += 1

    for index, company in enumerate(queryset):
        start_row_num += 1

        worksheet.write(start_row_num, 0, index, center_data)
        worksheet.write(start_row_num, 1, company.id, center_data)
        worksheet.write(start_row_num, 2, company.type, center_data)
        worksheet.write(start_row_num, 3, company.name, center_data)
        worksheet.write(start_row_num, 4, company.business_opening_at, center_data)
        worksheet.write(start_row_num, 5, company.business_registration_number, center_data)
        worksheet.write(start_row_num, 6, company.email, center_data)
        worksheet.write(start_row_num, 7, company.address, center_data)
        worksheet.write(start_row_num, 8, company.representative_name, center_data)
        worksheet.write(start_row_num, 9, company.representative_number, center_data)
        worksheet.write(start_row_num, 10, company.company_number, center_data)
        worksheet.write(start_row_num, 11, company.person_in_charge, center_data)
        worksheet.write(start_row_num, 12, company.person_in_charge_position, center_data)
        worksheet.write(start_row_num, 13, company.person_in_charge_number, center_data)

        worksheet.write(start_row_num, 14, company.evaluation_count_current_month, center_data)
        worksheet.write(start_row_num, 15, company.inspection_count_current_month, center_data)
        worksheet.write(start_row_num, 16, company.delivery_count_current_month, center_data)
        worksheet.write(start_row_num, 17, company.total_count_current_month, center_data)

        worksheet.write(start_row_num, 18, company.evaluation_count_avg_3_month, center_data)
        worksheet.write(start_row_num, 19, company.inspection_count_avg_3_month, center_data)
        worksheet.write(start_row_num, 20, company.delivery_count_avg_3_month, center_data)
        worksheet.write(start_row_num, 21, company.total_count_avg_3_month, center_data)

        worksheet.write(start_row_num, 22, company.evaluation_costs_current_month, center_data)
        worksheet.write(start_row_num, 23, company.inspection_costs_current_month, center_data)
        worksheet.write(start_row_num, 24, company.delivery_costs_current_month, center_data)
        worksheet.write(start_row_num, 25, company.total_costs_current_month, center_data)

        worksheet.write(start_row_num, 26, company.evaluation_costs_avg_3_month, center_data)
        worksheet.write(start_row_num, 27, company.inspection_costs_avg_3_month, center_data)
        worksheet.write(start_row_num, 28, company.delivery_costs_avg_3_month, center_data)
        worksheet.write(start_row_num, 29, company.total_costs_avg_3_month, center_data)

        worksheet.write(start_row_num, 30, company.acc_evaluation_costs, center_data)
        worksheet.write(start_row_num, 31, company.acc_inspection_costs, center_data)
        worksheet.write(start_row_num, 32, company.acc_delivery_costs, center_data)
        worksheet.write(start_row_num, 33, company.acc_total_costs, center_data)

    workbook.close()

    output.seek(0)

    return output

