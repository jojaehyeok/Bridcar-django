REQUESTING_TYPES = (
    ('EVALUATION_DELIVERY', '평카 탁송'),
    ('INSPECTION_DELIVERY', '검수 탁송'),
    ('ONLY_DELIVERY', '일반 탁송'),
)

REQUESTING_STATUS = (
    ('WAITING_AGENT', '평카인 배정 대기'),
    ('WAITING_WORKING', '업무 시작 대기'),
    ('EVALUATING', '평카/검수중'),
    ('EVALUATION_DONE', '평카/검수 완료'),
    ('WAITING_DELIVERER', '탁송 기사 배정 대기'),
    ('WAITING_DELIVERY_WORKING', '탁송 시작 대기'),
    ('DELIVERING', '탁송중'),
    ('DELIVERING_DONE', '탁송 완료'),
    ('CANCELLED', '서비스 취소'),
    ('DONE', '서비스 완료'),
)

DELIVERY_REQUESTING_STATUS = REQUESTING_STATUS[4:]
WORKING_REQUESTING_STATUS_KEYS = list(dict(REQUESTING_STATUS).keys())[:8]

REQUESTING_CHATTING_SENDING_TO = (
    ( 'client', '딜러에게 보낸 메시지' ),
    ( 'agent', '평카인에게 보낸 메시지' ),
    ( 'deliverer', '탁송기사에게 보낸 메시지' ),
)

ADDITIONAL_COST_TYPES = (
    ('주유비', '주유비'),
    ('대기비', '대기비'),
    ('기타', '기타'),
)

ADDITIONAL_COST_WORKING_TYPES = (
    ( 'EVALUATION/INSPECTION', '평카/검수' ),
    ( 'DELIVERY', '탁송' ),
)

CAR_BASIC_IMAGE_TYPES = (
    ( 'CAR_KEY', '차키' ),
    ( 'DASHBOARD', '계기판' ),
    ( 'EXTERIOR', '외장' ),
    ( 'INTERIOR', '내장' ),
    ( 'WHEEL', '휠' ),
    ( 'DAMAGED_PARTS', '사고 부위' ),
    ( 'REQUIRED_DOCUMENTS', '명의이전 구비서류' ),
    ( 'ETC', '기타' ),
)
