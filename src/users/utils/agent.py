import io
import json
import base64
import requests

import xlsxwriter

from django.conf import settings


def generate_agent_list_xlsx(queryset):
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output)

    workbook.formats[0].set_font_size(11)
    workbook.formats[0].set_font_name('맑은 고딕')

    worksheet = workbook.add_worksheet()

    for i in range(1, 42):
        if i == 1:
            worksheet.set_column(i, i, 30)

        worksheet.set_column(i, i, 18)

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

    yellow_merge_format = workbook.add_format({
        'bg_color': '#FDEADA',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
    })

    yellow_th_bold_format = workbook.add_format({
        'bold': 1,
        'bg_color': '#FDEADA',
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

    worksheet.merge_range('A4:N4', '평가사 회원 기본정보', basic_merge_format)
    worksheet.write(start_row_num, 14, '보험료', yellow_merge_format)
    worksheet.merge_range('P4:Q4', '차감내역 및 입출금내역', basic_merge_format)
    worksheet.merge_range('R4:U4', '고정평가 평가사 정보', yellow_merge_format)
    worksheet.merge_range('V4:Y4', '경력사항', basic_merge_format)
    worksheet.merge_range('Z4:AB4', '월 평균 건수 (최근 3개월)', yellow_merge_format)
    worksheet.merge_range('AC4:AH4', '평가사 레벨', basic_merge_format)
    worksheet.merge_range('AI4:AP4', '평가사 교육과정 정보', yellow_merge_format)

    worksheet.write(start_row_num + 1, 0, '순번', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 1, '평가사 코드번호', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 2, '생년월일', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 3, '주소', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 4, '은행명', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 5, '계좌번호', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 6, '예금주', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 7, '성명', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 8, '소속지역', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 9, '평가사 등급', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 10, '활동 현황', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 11, '평가사 교육 시작일', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 12, '평가사 교육 수료일', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 13, '최초 근무 시작일', basic_th_bold_format)

    worksheet.write(start_row_num + 1, 14, '월 보험금', yellow_th_bold_format)

    worksheet.write(start_row_num + 1, 15, '현 적립금', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 16, '월 평균 출금액 (3개월)', basic_th_bold_format)

    worksheet.write(start_row_num + 1, 17, '최초근무지역', yellow_th_bold_format)
    worksheet.write(start_row_num + 1, 18, '현근무지', yellow_th_bold_format)
    worksheet.write(start_row_num + 1, 19, '휴무 요일', yellow_th_bold_format)
    worksheet.write(start_row_num + 1, 20, '현 주말전담반 근무지역', yellow_th_bold_format)

    worksheet.write(start_row_num + 1, 21, '평가', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 22, '검수', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 23, '탁송', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 24, '평가사 홍보', basic_th_bold_format)

    worksheet.write(start_row_num + 1, 25, '평가', yellow_th_bold_format)
    worksheet.write(start_row_num + 1, 26, '검수', yellow_th_bold_format)
    worksheet.write(start_row_num + 1, 27, '탁송', yellow_th_bold_format)

    worksheet.write(start_row_num + 1, 28, '평가', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 29, '검수', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 30, '탁송', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 31, 'CS (고객응대 수준)', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 32, '시간 준수수준', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 33, '도토리 (기여도) 현황', basic_th_bold_format)

    worksheet.write(start_row_num + 1, 34, '성향/성격', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 35, '이웃친밀도', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 36, '교육참여도', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 37, '교육습득능력', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 38, '보수교육(회)', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 39, '집체교육(회)', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 40, '교육등급', basic_th_bold_format)
    worksheet.write(start_row_num + 1, 41, '수료 테스트 결과', basic_th_bold_format)


    start_row_num += 1

    for index, agent in enumerate(queryset):
        start_row_num += 1

        agent_settlement_account = getattr(agent, 'agent_settlement_account', None)

        worksheet.write(start_row_num, 0, index + 1, center_data)
        worksheet.write(start_row_num, 1, agent.agent_profile.id, center_data)
        worksheet.write(start_row_num, 2, agent.agent_profile.birthday, center_data)
        worksheet.write(start_row_num, 3, agent.agent_profile.home_address, center_data)
        worksheet.write(start_row_num, 4, agent_settlement_account.bank_name if agent_settlement_account != None else '', center_data)
        worksheet.write(start_row_num, 5, agent_settlement_account.account_number if agent_settlement_account != None else '', center_data)
        worksheet.write(start_row_num, 6, agent_settlement_account.account_holder if agent_settlement_account != None else '', center_data)
        worksheet.write(start_row_num, 7, agent.name, center_data)
        worksheet.write(start_row_num, 8, agent.agent_profile.affiliated_area, center_data)
        worksheet.write(start_row_num, 9, agent.agent_profile.level, center_data)
        worksheet.write(start_row_num, 10, ''.join(agent.agent_profile.activity_areas), center_data)
        worksheet.write(start_row_num, 11, agent.agent_profile.training_start_date, center_data)
        worksheet.write(start_row_num, 12, agent.agent_profile.training_completion_date, center_data)
        worksheet.write(start_row_num, 13, agent.agent_profile.first_working_start_date, center_data)

        worksheet.write(start_row_num, 14, agent.agent_profile.monthly_insurance_cost, center_data)

        worksheet.write(start_row_num, 15, agent.agent_profile.balance, center_data)
        worksheet.write(start_row_num, 16, agent.avg_3month_withdrawal_amount, center_data)

        worksheet.write(start_row_num, 17, agent.agent_profile.first_working_area, center_data)
        worksheet.write(start_row_num, 18, agent.agent_profile.current_working_area, center_data)
        worksheet.write(start_row_num, 19, agent.agent_profile.closed_days, center_data)
        worksheet.write(start_row_num, 20, agent.agent_profile.weekend_charge_working_area, center_data)

        worksheet.write(start_row_num, 21, agent.agent_profile.total_evaluation_count, center_data)
        worksheet.write(start_row_num, 22, agent.agent_profile.total_inspection_count, center_data)
        worksheet.write(start_row_num, 23, agent.agent_profile.total_delivery_count, center_data)
        worksheet.write(start_row_num, 24, agent.agent_profile.total_marketing_count, center_data)

        worksheet.write(start_row_num, 25, agent.evaluation_count_avg_3_month, center_data)
        worksheet.write(start_row_num, 26, agent.inspection_count_avg_3_month, center_data)
        worksheet.write(start_row_num, 27, agent.delivery_count_avg_3_month, center_data)

        worksheet.write(start_row_num, 28, agent.agent_profile.evaluation_score, center_data)
        worksheet.write(start_row_num, 29, agent.agent_profile.inspection_score, center_data)
        worksheet.write(start_row_num, 30, agent.agent_profile.delivery_score, center_data)
        worksheet.write(start_row_num, 31, agent.agent_profile.cs_score, center_data)
        worksheet.write(start_row_num, 32, agent.agent_profile.appointment_time_score, center_data)
        worksheet.write(start_row_num, 33, agent.agent_profile.dotori_status, center_data)

        worksheet.write(start_row_num, 34, agent.agent_profile.tendency, center_data)
        worksheet.write(start_row_num, 35, agent.agent_profile.intimacy, center_data)
        worksheet.write(start_row_num, 36, agent.agent_profile.education_participation, center_data)
        worksheet.write(start_row_num, 37, agent.agent_profile.ability_to_acquire_education, center_data)
        worksheet.write(start_row_num, 38, agent.agent_profile.supplementary_education_count, center_data)
        worksheet.write(start_row_num, 39, agent.agent_profile.collective_education_count, center_data)
        worksheet.write(start_row_num, 40, agent.agent_profile.education_grade, center_data)
        worksheet.write(start_row_num, 41, agent.agent_profile.completion_test_result, center_data)

    workbook.close()

    output.seek(0)

    return output

