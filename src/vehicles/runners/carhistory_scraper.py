import re
import os
import time
import json
import logging
import asyncio
import subprocess

from datetime import datetime

from django.conf import settings
from django.utils import timezone

from asgiref.sync import sync_to_async

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from requestings.models import RequestingHistory

from vehicles.models import Car, CarhistoryResult, CarhistoryAccidentInsuranceHistory, \
                            CarhistoryOwnerChangeHistory

from pcar.utils import RedisQueue


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='/home/api-server/logs/carhistory_scraper.log'
)


class CarHistoryError(Exception):
    def __init__(self, detail):
        self.detail = detail

class CarHistoryInformation:

    error_message = ''

    def __init__(self, id, pw, carnum, is_debug=False):
        self._id = id
        self._pw = pw
        self._carnum = carnum

        self.result = {
            'initialized': False,
            'summary': {
                'total_loss': 0,
                'theft': 0,
                'flooding': False,
                'special_use': False,
                'owner_changed': 0,
                'num_changed': 0,
                'my_damage': {
                    'count': 0,
                    'price': 0,
                },
                'opposite_damage': {
                    'count': 0,
                    'price': 0,
                }
            },
            'spec': {
                'manufacturer': '',
                'model_name': '',
                'displacement': 0,
                'fuel_type': '',
                'model_year': '',
                'initial_insurance_at': None
                # @TODO:
                # 차체형상
                # 용도 및 차종
                # 위 정보는 파싱이 곤란하기 때문에 우선 생략
            },
            'change_histories': [
                #{
                #    changed_at: None,
                #    changed_usage: '',
                #    changed_reason: '',
                #    changed_carnum: '',
                #}
            ],
            'insurance_accident_histories': [
                #{
                #    'insurance_at': None,
                #    'my_damage': {
                #        'my_insurance': { 내용이 없으면 이 dict 가 없을수도 있음
                #            'total_cost': 0,
                #            'parts_cost': 0,
                #            'labor_cost': 0,
                #            'painting_cost': 0,
                #        },
                #        'opposite_insurance': { 내용이 없으면 이 dict 가 없을수도 있음
                #            'total_cost': 0,
                #            'parts_cost': 0,
                #            'labor_cost': 0,
                #            'painting_cost': 0,
                #        }
                #    },
                #    'opposite_damage': {
                #        'my_insurance': { 내용이 없으면 이 dict 가 없을수도 있음
                #            'total_cost': 0,
                #            'parts_cost': 0,
                #            'labor_cost': 0,
                #            'painting_cost': 0,
                #        }
                #    }
                #}
            ]
        }

        options = webdriver.ChromeOptions()

        options.add_argument('headless')
        options.add_argument('incognito')
        options.add_argument('ignore-certificate-errors')
        options.add_argument('no-sandbox')
        options.add_argument('screen-size=1920x1080')
        options.add_argument('window-size=1920x1080')

        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
        options.add_argument('user-agent=' + user_agent)

        if is_debug:
            import chromedriver_autoinstaller

            subprocess.Popen(r'/opt/google/chrome/google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome-debug"', shell=True)

            options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')

            chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
            driver_path = f'./{ chrome_ver }/chromedriver'

            if not os.path.exists(driver_path):
                chromedriver_autoinstaller.install(True)

            self.driver = webdriver.Chrome(driver_path, options=options)
        else:
            self.driver = webdriver.Remote(
                command_executor='http://selenium-hub:4444/wd/hub',
                options=options,
            )

    def _check_exists_by_xpath(self, xpath):
        try:
            self.driver.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            return False

        return True

    def initialize_information_page(self):
        is_login_require = True

        self.driver.maximize_window()

        self.driver.get('https://www.carhistory.or.kr')
        self.driver.implicitly_wait(15)

        while len(self.driver.page_source) < 300:
            self.driver.refresh()
            self.driver.implicitly_wait(15)

        with open('/home/api-server/logs/carhistory_page_initial.html', 'w') as file:
            file.write(self.driver.page_source)

        try:
            element = self.driver.find_element(By.XPATH, '//a[text()="충전회원"]')
            element.click()
        except Exception as e:
            is_login_require = False

        try:
            if is_login_require:
                self.driver.find_element(By.ID, 'id').send_keys(self._id)
                self.driver.find_element(By.ID, 'pwd').send_keys(self._pw)

                self.driver.find_element(By.XPATH, '//button[text()="로그인"]').click()
                self.driver.implicitly_wait(15)

            self.driver.find_element(By.ID, 'carnum').send_keys(self._carnum)
            self.driver.find_element(By.ID, 'searchBtn').click()
            self.driver.find_element(By.ID, 'allAgree').click()

            try:
                self.driver.find_element(By.XPATH, '//h2[@class="title" and text()="차량번호 오류"]')

                raise CarHistoryError('INVALID_CAR_NUMBER')
            except NoSuchElementException:
                pass

            with open('/home/api-server/logs/carhistory_page_free_payment.html', 'w') as file:
                file.write(self.driver.page_source)

            try:
                self.driver.find_element(By.XPATH, '//a[contains(@href, "hourcheck")]').click()
                self.driver.implicitly_wait(15)

                while len(self.driver.page_source) < 200:
                    self.driver.refresh()
                    self.driver.implicitly_wait(15)
            except NoSuchElementException:
                self.driver.implicitly_wait(15)
                is_payment_page = self._check_exists_by_xpath('//div[@id="select-pay-type"]')

                with open('/home/api-server/logs/carhistory_page_payment.html', 'w') as file:
                    file.write(self.driver.page_source)

                if is_payment_page:
                    self.driver.find_element(By.XPATH, '//input[@type="radio"][@id="point"]/following-sibling::label[@for="point"]').click()

                    time.sleep(0.5)

                    if int(self.driver.find_element(By.ID, 'pointBonus').text.replace(',', ''), 10) < 100:
                        raise CarHistoryError("NOT_ENOUGH_POINT")

                    self.driver.find_element(By.ID, 'pwd').send_keys(self._pw)
                    self.driver.execute_script('use_point("Y")')

                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    self.driver.find_element(By.XPATH, '//input[@type="checkbox"][@id="ok"]/following-sibling::label[@for="ok"]').click()
                    self.driver.execute_script('goCoupon()')
                else:
                    self.driver.implicitly_wait(15)
                    self.driver.find_element(By.XPATH, '//button[text()="확인"]').click()
                    #self.driver.execute_script('showReport2()')
                    #driver.find_element('//a[text()="포인트 사용"]').click()

            self.result['initialized'] = True
        except (CarHistoryError, Exception) as e:
            with open('/home/api-server/logs/last_carhistory_page_initial.html', 'w') as file:
                file.write(self.driver.page_source)

            self.clean_up()
            self.error_message = str(e)

            raise e

    def clean_up(self):
        self.driver.quit()

    def get_summary_informations(self):
        count_regex = re.compile(r'([0-9]+)회')

        total_loss = \
            self.driver.find_element(By.XPATH, '//span[text()="전손 보험사고"]/following-sibling::div/strong').text

        searched_total_loss = count_regex.search(total_loss)

        if searched_total_loss:
            self.result['summary']['total_loss'] = int(
                searched_total_loss.group(1),
                10
            )
        else:
            self.result['summary']['total_loss'] = 0

        theft = \
            self.driver.find_element(By.XPATH, '//span[text()="도난 보험사고"]/following-sibling::div/strong').text

        searched_theft = count_regex.search(theft)

        if searched_theft:
            self.result['summary']['theft'] = int(
                searched_theft.group(1),
                10
            )
        else:
            self.result['summary']['theft'] = 0

        flooding = \
            self.driver.find_element(By.XPATH, '//span[text()="침수 보험사고"]/following-sibling::div/strong').text

        self.result['summary']['flooding'] = \
            True if flooding == '있음' else False

        special_use = \
            self.driver.find_element(By.XPATH, '//span[text()="특수 용도 이력"]/following-sibling::div/strong').text

        self.result['summary']['special_use'] = \
            True if special_use == '있음' else False

        my_damage_count = self.driver.find_element(By.XPATH, '//span[text()="내차 피해"]/following-sibling::div/strong[1]').text

        if my_damage_count != '없음':
            self.result['summary']['my_damage']['count'] = int(my_damage_count, 10)

            self.result['summary']['my_damage']['price'] = \
                re.sub(
                    r'원|\(|\)|,|\s',
                    '',
                    self.driver.find_element(By.XPATH, '//span[text()="내차 피해"]/following-sibling::div/strong[2]').text
                )

        opposite_damage_count = self.driver.find_element(By.XPATH, '//span[text()="상대차 피해"]/following-sibling::div/strong[1]').text

        if opposite_damage_count != '없음':
            self.result['summary']['opposite_damage']['count'] = int(opposite_damage_count, 10)

            self.result['summary']['opposite_damage']['price'] = \
                re.sub(
                    r'\+미확정',
                    '',
                    re.sub(
                        r'원|\(|\)|,|\s',
                        '',
                        self.driver.find_element(By.XPATH, '//span[text()="상대차 피해"]/following-sibling::div/strong[2]').text
                    )
                )

        self.result['summary']['owner_changed'] = \
            int(
                re.sub(
                    r'회',
                    '',
                    self.driver.find_element(By.XPATH, '//span[text()="소유자 변경"]/following-sibling::div/strong').text
                ), 10
            )

        self.result['summary']['num_changed'] = \
            int(
                re.sub(
                    r'회',
                    '',
                    self.driver.find_element(By.XPATH, '//span[text()="차량번호 변경"]/following-sibling::div/strong').text
                ), 10
            )

    def get_spec_informations(self):
        self.result['spec']['manufacturer'] = \
            self.driver.find_element(By.XPATH, '//th[text()="제조사"]/following-sibling::td').text

        self.result['spec']['model_name'] = \
            self.driver.find_element(By.XPATH, '//th[text()="자동차명"]/following-sibling::td').text

        self.result['spec']['displacement'] = \
            int(
                re.sub(
                    'cc|,',
                    '',
                    self.driver.find_element(By.XPATH, '//th[text()="배기량"]/following-sibling::td').text
                ), 10
            )

        self.result['spec']['fuel_type'] = \
            self.driver.find_element(By.XPATH, '//th[text()="사용연료"]/following-sibling::td').text

        self.result['spec']['model_year'] = \
            self.driver.find_element(By.XPATH, '//th[text()="연식(Model year)"]/following-sibling::td').text

        self.result['spec']['initial_insurance_at'] = \
            datetime.strptime(
                self.driver.find_element(By.XPATH, '//th[text()="최초 보험 가입일자"]/following-sibling::td').text,
                '%Y년 %m월 %d일'
            )

    def get_change_owner_histories(self):
        change_owner_histories = \
            self.driver.find_elements(By.XPATH, '//div[@id="report4"]/div[@class="responsive-table"]/div[@class="tb-body tb-row"]')

        for history in change_owner_histories:
            change_history = {}

            change_history['changed_at'] = \
                datetime.strptime(
                    history.find_element(By.XPATH, '//div[@class="td date"]').text,
                    '%Y-%m-%d'
                )

            other_change_history = history.find_elements(By.XPATH, './/div[@class="td"]')
            change_history['changed_reason'] = other_change_history[0].text
            change_history['changed_carnum'] = other_change_history[1].text
            change_history['changed_usage'] = other_change_history[2].text

            self.result['change_histories'].append(change_history)

    def __get_insurance_costs(self, history_text):
        parts_regex = re.compile(r'부품 : (([0-9]{1,3}[,|원])+)')
        labor_regex = re.compile(r'공임 : (([0-9]{1,3}[,|원])+)')
        painting_regex = re.compile(r'도장 : (([0-9]{1,3}[,|원])+)')

        parts_cost = int(re.sub(',|원', '', parts_regex.search(history_text).group(1)), 10)
        labor_cost = int(re.sub(',|원', '', labor_regex.search(history_text).group(1)), 10)
        painting_cost = int(re.sub(',|원', '', painting_regex.search(history_text).group(1)), 10)

        return [ parts_cost, labor_cost, painting_cost ]

    def get_insurance_accident_histories(self):
        insurance_accident_histories = \
            self.driver.find_elements(By.XPATH, '//div[@class="crash-info-list"]')

        for accident in insurance_accident_histories:
            insurance_accident = {
            }

            insurance_accident['insurance_at'] = \
                datetime.strptime(
                    accident.find_element(By.XPATH, './/div[@class="color-key xlarge"]').text,
                    '%Y-%m-%d'
                )

            histories = accident.find_elements(By.XPATH, './/td[@class="text-center"]')

            if re.sub(r'\s', '', histories[0].text) != "":
                if 'my_damage' not in insurance_accident:
                    insurance_accident['my_damage'] = {}

                insurance_accident['my_damage']['my_insurance'] = {}

                insurance_accident['my_damage']['my_insurance']['total_cost'] = \
                    int(
                        re.sub(',', '', histories[0].find_element(By.XPATH, './/strong[@class="color-key"]').text),
                        10
                    )

                parts_cost, labor_cost, painting_cost = self.__get_insurance_costs(histories[0].text)

                insurance_accident['my_damage']['my_insurance']['parts_cost'] = parts_cost
                insurance_accident['my_damage']['my_insurance']['labor_cost'] = labor_cost
                insurance_accident['my_damage']['my_insurance']['painting_cost'] = painting_cost

            if re.sub(r'\s', '', histories[1].text) != "":
                if 'my_damage' not in insurance_accident:
                    insurance_accident['my_damage'] = {}

                insurance_accident['my_damage']['opposite_insurance'] = {}

                insurance_accident['my_damage']['opposite_insurance']['total_cost'] = \
                    int(
                        re.sub(',', '', histories[1].find_element(By.XPATH, './/strong[@class="color-key"]').text),
                        10
                    )

                parts_cost, labor_cost, painting_cost = self.__get_insurance_costs(histories[1].text)

                insurance_accident['my_damage']['opposite_insurance']['parts_cost'] = parts_cost
                insurance_accident['my_damage']['opposite_insurance']['labor_cost'] = labor_cost
                insurance_accident['my_damage']['opposite_insurance']['painting_cost'] = painting_cost

            if re.sub(r'\s', '', histories[2].text) != "":
                if 'opposite_damage' not in insurance_accident:
                    insurance_accident['opposite_damage'] = {}

                insurance_accident['opposite_damage']['my_insurance'] = {}

                if re.sub(',', '', histories[2].find_element(By.XPATH, './/strong[@class="color-green"]').text) == '미확정':
                    continue
                else:
                    insurance_accident['opposite_damage']['my_insurance']['total_cost'] = \
                        int(
                            re.sub(',', '', histories[2].find_element(By.XPATH, './/strong[@class="color-green"]').text),
                            10
                        )

                    parts_cost, labor_cost, painting_cost = self.__get_insurance_costs(histories[2].text)

                    insurance_accident['opposite_damage']['my_insurance']['parts_cost'] = parts_cost
                    insurance_accident['opposite_damage']['my_insurance']['labor_cost'] = labor_cost
                    insurance_accident['opposite_damage']['my_insurance']['painting_cost'] = painting_cost

            self.result['insurance_accident_histories'].append(insurance_accident)

    def get_full_informations(self):
        try:
            if self.result['initialized'] == False:
                self.initialize_information_page()

            self.get_summary_informations()
            self.get_spec_informations()
            self.get_change_owner_histories()
            self.get_insurance_accident_histories()

            self.clean_up()
            self.error_message = ''
        except (CarHistoryError, Exception) as e:
            with open('/home/api-server/logs/last_carhistory_page.html', 'w') as file:
                file.write(self.driver.page_source)

            self.clean_up()
            self.error_message = str(e)

            raise e

def save_carhistory_result(requesting_history_id, scrapped_carhistory):
    requesting_history = RequestingHistory.objects.filter(pk=requesting_history_id).first()

    if requesting_history == None:
        return

    car = requesting_history.car
    carhistory_result = car.carhistory_result

    carhistory_result.is_scrapping = False
    carhistory_result.scrapping_at = timezone.now()

    if scrapped_carhistory.error_message != '':
        carhistory_result.error_message = scrapped_carhistory.error_message
    else:
        scrapped_carhistory_result = scrapped_carhistory.result

        carhistory_result.insurance_with_my_damages.all().delete()
        carhistory_result.insurance_with_opposite_damages.all().delete()
        carhistory_result.owner_change_histories.all().delete()

        for owner_change_history in scrapped_carhistory_result['change_histories']:
            CarhistoryOwnerChangeHistory.objects.create(
                carhistory_result=carhistory_result,
                changed_at=owner_change_history['changed_at'],
                changing_type=owner_change_history['changed_reason'],
                changing_usage=owner_change_history['changed_usage'],
                changed_car_number=owner_change_history['changed_carnum'],
            )

        for insurance_history in scrapped_carhistory_result['insurance_accident_histories']:
            my_damage = insurance_history.get('my_damage', None)
            opposite_damage = insurance_history.get('opposite_damage', None)

            if my_damage != None:
                if my_damage.get('my_insurance', None) != None:
                    carhistory_result.insurance_with_my_damages.add(
                        CarhistoryAccidentInsuranceHistory.objects.create(
                            insurance_at=insurance_history['insurance_at'],
                            total_cost=my_damage['my_insurance']['total_cost'],
                            parts_cost=my_damage['my_insurance']['parts_cost'],
                            labor_cost=my_damage['my_insurance']['labor_cost'],
                            painting_cost=my_damage['my_insurance']['painting_cost'],
                        )
                    )

                if my_damage.get('opposite_insurance', None) != None:
                    carhistory_result.insurance_with_my_damages.add(
                        CarhistoryAccidentInsuranceHistory.objects.create(
                            insurance_at=insurance_history['insurance_at'],
                            total_cost=my_damage['opposite_insurance']['total_cost'],
                            parts_cost=my_damage['opposite_insurance']['parts_cost'],
                            labor_cost=my_damage['opposite_insurance']['labor_cost'],
                            painting_cost=my_damage['opposite_insurance']['painting_cost'],
                        )
                    )

            if opposite_damage != None and opposite_damage.get('my_insurance', None) != None:
                carhistory_result.insurance_with_opposite_damages.add(
                    CarhistoryAccidentInsuranceHistory.objects.create(
                        insurance_at=insurance_history['insurance_at'],
                        total_cost=opposite_damage['my_insurance']['total_cost'],
                        parts_cost=opposite_damage['my_insurance']['parts_cost'],
                        labor_cost=opposite_damage['my_insurance']['labor_cost'],
                        painting_cost=opposite_damage['my_insurance']['painting_cost'],
                    )
                )

    carhistory_result.save()

async def main():
    rq = RedisQueue('carhistory_scraper')

    while True:
        new_requesting = None
        car_info = None

        try:
            new_requesting = json.loads(await rq.get(isBlocking=True))
        except Exception as e:
            logging.critical(e, exc_info=True)
            continue

        logging.info(f'차량번호 { new_requesting["car_number"] } 조회 시작')

        car_info = CarHistoryInformation(
            id=settings.CARHISTORY_ID,
            pw=settings.CARHISTORY_PASSWORD,
            carnum=new_requesting['car_number'],
            is_debug=False
        )

        try:
            car_info.get_full_informations()

            logging.info(f'차량번호 { new_requesting["car_number"] } 조회 완료')
        except (CarHistoryError, Exception) as e:
            if isinstance(e, CarHistoryError):
                if e.detail == 'INVALID_CAR_NUMBER':
                    car_info.error_message = '잘못된 차량 번호입니다.'
                    logging.error('잘못된 차량 번호입니다')
                elif e.detail == 'NOT_ENOUGH_POINT':
                    car_info.error_message = '포인트가 부족합니다.'
                    logging.error('포인트가 부족합니다')
            else:
                logging.error('초기화 과정에서 오류가 있습니다')
                logging.error(e, exc_info=True)

        await sync_to_async(save_carhistory_result)(new_requesting['requesting_id'], car_info)

        del car_info

        time.sleep(1)

asyncio.run(main())
