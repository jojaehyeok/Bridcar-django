SMS_AUTHENTICATION_PURPOSES = (
    ('signin', '로그인'),
    ('control_room_signin', '로그인'),
    ('signup', '회원가입'),
    ('find_email', '이메일 찾기'),
    ('find_password', '비밀번호 찾기'),
    ('change_mobile_number', '핸드폰 번호 변경'),
)

AGENT_LEVEL = (
    ('A', 'A레벨'),
    ('B', 'B레벨'),
    ('C', 'C레벨'),
)

AGENT_REVIEW_LEVEL = (
    ('상', '상'),
    ('중', '중'),
    ('하', '하'),
)

AGENT_TEST_RESULTS = (
    ('초급', '초급'),
    ('중급', '중급'),
    ('고급', '고급'),
)

AGENT_ACTIVITY_AREAS = (
    ( 'zero 평가인', 'zero 평가인', ),
    ( '평가', '평가', ),
    ( '평카탁송', '평가탁송', ),
    ( '검수탁송', '검수탁송', ),
    ( '일반탁송', '일반탁송', ),
    ( '홍보 (영업)', '홍보 (영업)', ),
    ( '기타', '기타', ),
)

BALANCE_HISTORY_TYPE = (
    ( 'manual_deposit', '수동 입금' ),
    ( 'deposit', '가상계좌 입금' ),
    ( 'withdrawal', '출금' ),
    ( 'revenue', '수익금 입금' ),
    ( 'referer_revenue', '홍보 수익금 입금' ),
    ( 'fee_escrow', '수수료 에스크로' ),
    ( 'fee_refund', '수수료 환불' ),
)

BALANCE_HISTORY_SUB_TYPES = (
    ( 'agent', '에이전트 수수료 구분용 (평카/검수)' ),
    ( 'deliverer', '탁송기사 수수료 구분용' ),
)

DEALER_BUSINESS_ITEMS = (
    ( '평가', '평가', ),
    ( '검수', '검수', ),
    ( '탁송', '탁송', ),
    ( '중개', '중개', ),
)

DEALER_BUSINESS_CATEGORIES = (
    ( '중고차 매매업', '중고차 매매업' ),
    ( '신차매매업', '신차매매업' ),
    ( '중고차딜러', '중고차딜러' ),
    ( '신차딜러', '신차딜러' ),
    ( '렌트카', '렌트카' ),
    ( '선물사 (리스, 채권)', '선물사 (리스, 채권)' ),
    ( '수출', '수출' ),
    ( '기타', '기타' ),
)

DEALER_COMPANY_TYPES = (
    ( '딜러', '딜러', ),
    ( '상사', '상사', ),
    ( '공업사', '공업사', ),
    ( '캠핑카', '캠핑카', ),
    ( '튜닝', '튜닝', ),
    ( '용품', '용품', ),
    ( '정비', '정비', ),
    ( '렌트', '렌트', ),
    ( '법인', '법인', ),
    ( '리스', '리스', ),
)

TOSS_PAYMENTS_VIRTUAL_ACCOUNT_BANKS = (
    ( '경남', 'KYONGNAMBANK', ),
    ( '광주', 'GWANGJUBANK', ),
    ( '국민', 'KOOKMIN', ),
    ( '기업', 'IBK', ),
    ( '농협', 'NONGHYEOP', ),
    ( '대구', 'DAEGUBANK', ),
    ( '부산', 'BUSANBANK', ),
    ( '새마을', 'SAEMAUL', ),
    ( '수협', 'SUHYEOP', ),
    ( '신한', 'SHINHAN', ),
    ( '우리', 'WOORI', ),
    ( '우체국', 'POST', ),
    ( '전북', 'JEONBUKBANK', ),
    ( '케이', 'KBANK', ),
    ( '하나', 'HANA', ),
)

API_USAGE_TYPES = (
    ( 'DAANGN', '당근마켓', ),
    ( 'OTHERS', '기타', )
)
