import logging
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait as Wait


# Mysuni 실행용 쓰레드 클래스
class MySuniWorker(QThread):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # self.timerEvent()

    # def setLogger(self, logging):
    #     self.logging = logging

    def run(self):
        logging.info('Start MySuni Thread...')
        logging.info('Badge Mode 는 도전중 Badge를 자동으로 실행합니다.')
        logging.info('Card Mode 는 Card 에 진입하는 시점부터 자동 실행이 시작됩니다.')
        logging.info('VR컨텐츠는 자동재생이 되지 않습니다.')
        self.start_mysuni()

    # def start_mysuni(site_urls):
    def start_mysuni(self):
        if self.parent.rb_badge.isChecked():
            self.classType = 'badge'
        else:
            self.classType = 'card'
        self.max_hour = int(self.parent.sb_hourlimit.text())
        self.b_mute = False
        self.my_suni_id = self.parent.le_id.text()
        self.my_suni_passwd = self.parent.le_pw.text()

        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(service=Service(executable_path=ChromeDriverManager().install()), options=options)
        self.driver = driver
        driver.implicitly_wait(10)

        # 프로그램 시작
        self.login_mysuni(driver, self.my_suni_id, self.my_suni_passwd)
        self.handle_of_the_window = driver.current_window_handle
        # 카드 선택인 경우
        if self.parent.rb_card.isChecked():
            while self.check_page(driver):
                time.sleep(10)
            logging.warning('Card 가 종료되었습니다.')
        # 배지 선택인 경우
        else:
            while self.check_badge(driver):
                time.sleep(10)
            logging.warning('Badge 가 종료되었습니다.')

        # 프로그램 끝
        driver.quit()
        if self.checkTimeOver():
            QtWidgets.QMessageBox.information(self.parent, "종료알림", "사용자가 설정한 제한 시간이 초과 되어 프로그램이 자동으로 종료됩니다.")
            logging.warning('사용자가 설정한 제한 시간이 초과 되어 프로그램이 자동으로 종료됩니다.')
            sys.exit()


    # 로그인 페이지
    def login_mysuni(self, driver, my_suni_id, my_suni_passwd):
        driver.get("https://mysuni.sk.com/")
        time.sleep(2)
        driver.find_element(By.NAME, "userID").send_keys(my_suni_id)
        driver.find_element(By.NAME, "password").send_keys(my_suni_passwd)
        driver.find_element(By.ID, "buttonLogin").click()
        time.sleep(2)


    # Case 1. 도전중 Badge 단위 실행
    def check_badge(self, driver):
        driver.get('https://mysuni.sk.com/suni-main/certification/badge/ChallengingBadgeList/pages/1')
        time.sleep(5)
        suni_getNextCard_string = """
        var tmp_badge = null;
        var el_next_card = null;
        var el_next_card_stat = null;
        var rtn_message = null;
        document.querySelectorAll('.challenge-badge .right-area').forEach(function(el) {
            tmp_badge = el.querySelector('.badge-title .t1').innerText + ' ' + el.querySelector(
            '.badge-title .t2').innerText;
            el.querySelectorAll('.challenge-list .class-card').forEach(function(el2) {
                el_next_card = el2.querySelector('.title').innerText;
                el_next_card_stat = el2.querySelector('tspan').innerHTML;
                if (el_next_card_stat != '학습완료') {
                    if (rtn_message == null){
                        rtn_message = '[' + tmp_badge + ']' + el2.querySelector('.title').innerText;
                    }
                }
            });
        });
        return rtn_message;
        """
        nextCard_info = driver.execute_script(suni_getNextCard_string)
        if nextCard_info is None:
            QtWidgets.QMessageBox.information(self.parent, "종료알림", "도전중인 Badge 가 없습니다. 프로그램을 종료합니다.")
            logging.warning('도전중인 Badge 가 없습니다. 프로그램을 종료합니다.')
            return False
        logging.info('Next Card: ' + nextCard_info)
        suni_runNextCard_string = """
        var tmp_badge = null;
        var el_next_card = null;
        var el_next_card_stat = null;
        var el_next_card_pointer = null;
        document.querySelectorAll('.challenge-badge .right-area').forEach(function (el) {
            tmp_badge = el.querySelector('.badge-title .t1').innerText + ' ' + el.querySelector('.badge-title .t2').innerText;
            el.querySelectorAll('.challenge-list .class-card').forEach(function (el2) {
                el_next_card = el2.querySelector('.title').innerText;
                el_next_card_stat = el2.querySelector('tspan').innerHTML;
                if(el_next_card_stat != '학습완료') {
                    if (el_next_card_pointer == null){
                        el_next_card_pointer = el2;
                    }
                }
            });
        });
        el_next_card_pointer.querySelector('a').click()
        """
        # Card 진입
        driver.execute_script(suni_runNextCard_string)
        time.sleep(5)
        return self.check_page(driver)


    # 창이 열려 있는지 확인
    # 헤더가 붙어 있는지 확인
    # 어느 페이지 인지 확인
    # 이 function 에서 False 를 반환하면 Chrome창을 닫고 Thread 를 종료한다는 의미이다.
    def check_page(self, driver):
        time.sleep(5)
        try:
            # 창이 열려 있는지 확인
            if driver:
                # 어느 페이지 인지 확인
                # 'mysuni.sk.com/suni-main/lecture/card/' 가 포함된 경우 카드 페이지
                if 'mysuni.sk.com/suni-main/lecture/card/' in driver.current_url:
                    # 카드 페이지라면 카드 강의를 시작한다.
                    # 카드 강의가 종료되어도 브라우저는 닫지 않으므로 True를 반환한다.
                    # 제한시간을 초과하면 False 를 반환한다.
                    return self.run_card(driver, driver.current_url, self.max_hour)
                else:
                    return True

            else:
                return False
        except BaseException as e:
            driver.quit()
            logging.warning('자동화 크롬 브라우저가 종료되었습니다.')
            return False


    # 남은 시간을 확인한다. 시간이 초과되면 True 를 반환한다.
    def checkTimeOver(self, nolog = False):
        elapsedTime = time.time() - self.parent.start_time
        if not nolog:
            logging.warning(f'Elapsed Time: {time.strftime("%Hh%Mm%Ss", time.gmtime(elapsedTime))}')
        if elapsedTime > self.max_hour * 3600:
            logging.warning('제한시간초과')
            return True
        else:
            return False


    # Case 2. 강의 단위 실행
    def run_card(self, driver, p_url, p_maxhour):
        # self.start_time = time.time() - 삭제예정
        # 간혹 일부 강의를 가져오지 못하는 경우가 있어 남은 강의가 없음을 확인후 종료
        b_haveMoreLecture = False
        while self.run_card_work(driver, p_url, p_maxhour) > 0:
            b_haveMoreLecture = True
        # 진행할 강의가 없거나 완료후 시간을 체크하여 시간이 지났으면 Thread 종료
        return b_haveMoreLecture and not self.checkTimeOver(nolog=True)

    # Case 2. 강의 단위 실행 - 세부 명령
    # 중간에 사용자의 입력이 있을수 있으므로 그때그때 하나씩 실행한다.
    def run_card_work(self, driver, p_url, p_maxhour):
        cnt_lecture = 0
        suni_query_string = """ var suni_card_list = document.querySelectorAll("div.state-course-holder a.btn-state-course");
                                var el_next_lecture = null;
                                var suni_lecture_list = [];
                                suni_card_list.forEach(function(element) {
                                    var el_title = element.querySelector(".copy-title").innerHTML;
                                    var el_link = 'https://mysuni.sk.com' + element.getAttribute('href');
                                    if (element.querySelector(".complete")) {
                                        suni_lecture_list.push('완료|'+el_title+'|'+el_link);
                                    } else {
                                        if (!el_next_lecture) {
                                            el_next_lecture = element;
                                            suni_lecture_list.push('다음|'+el_title+'|'+el_link);
                                        } else {
                                            suni_lecture_list.push('|'+el_title+'|'+el_link);
                                        }
                                    }
                                });
                                return suni_lecture_list;"""
        class_info = driver.execute_script(suni_query_string)
        class_info = [cinfo.split('|') for cinfo in class_info]

        for lecture_info in class_info:
            if cnt_lecture == 0 and lecture_info[0] != '완료':
                cnt_lecture += 1
                logging.warning(lecture_info[1] +' --> '+ lecture_info[2])
                url_str = lecture_info[2]
                if self.checkTimeOver():
                    return -1
                logging.warning(f'Next URL: {url_str}')
                # 만약 윈도우가 최소화된 경우 ActionChain을 사용할때 오류가 발생한다.
                # 자동으로 윈도우를 확대한다.
                if driver.execute_script('return document.hidden'):
                    driver.switch_to.window(self.handle_of_the_window)
                if time.perf_counter() < p_maxhour * 60 * 60:
                    if 'Video' in url_str:
                        try:
                            self.run_video(driver, url_str)
                        except BaseException as e:
                            logging.warning(e)
                            self._check_finish()
                    elif self.parent.cb_autodocument.isChecked() and 'Documents' in url_str:
                        try:
                            self.run_documents(driver, url_str)
                        except BaseException as e:
                            logging.warning(e)
                            self._check_finish()
                        # 강의 평가 이외의 Survey는 자동실행 대상에서 제외한다.
                    elif self.parent.cb_autosurvey.isChecked() and 'survey' in url_str and 'survey/' not in url_str:
                        self.run_survey(driver, url_str)
                    else:
                        self.run_selfStudy(driver, url_str)

        # exception 발생시 driver 체크후 class를 다시 돌려 lecture를 실행할 수 있도록 하는 루틴 추가 필요
        return cnt_lecture

    def run_selfStudy(self, driver, p_page_url):
        # 미지원 페이지 진입
        logging.info(f'Run Self Study: {p_page_url}')
        time.sleep(3)
        driver.get(p_page_url)
        time.sleep(5)
        self._check_finish()

    # Card 진행 - 비디오 페이지
    def run_video(self, driver, p_page_url):
        # 비디오 페이지 진입
        logging.info(f'Run Video: {p_page_url}')
        time.sleep(3)
        driver.get(p_page_url)
        time.sleep(5)

        # 만약 팝업창이 뜰 경우 자동 클릭
        self._check_popup()

        # 비디오 플레이어 작동을 위한 ActionChains 객체 생성
        action = ActionChains(driver)

        # 플레이버튼 클릭
        btn_area = driver.find_element(By.CSS_SELECTOR, "div.video-container .hover-area img")
        action.move_to_element(btn_area).click().perform()

        time.sleep(3)
        # 속도 조절
        video_area = driver.find_element(By.ID, "hover-area")
        action.move_to_element(video_area).perform()
        speed_menu = Wait(driver, 10).until(EC.element_to_be_clickable((By.ID, "playbackSpeedButton")))
        speed_menu.click()

        userSpeed = float(self.parent.dsb_videospeed.text())
        if userSpeed.is_integer():
            userSpeed = int(userSpeed)
        query_forVideoSpeed = f"""
        document.evaluate('//*[@id="playbackSpeedButton"]//*/dd/span[contains(.,"{userSpeed}")]', document, null,
                          XPathResult.ANY_TYPE, null).iterateNext().click()
                          """
        driver.execute_script(query_forVideoSpeed)
        # driver.find_element(By.CSS_SELECTOR, "div#playbackSpeedButton dd:nth-of-type(3) > span").click()
        # if b_mute:
        #     driver.find_element(By.ID, "muteButton").click()

        # 플레이 시작 - 끝날때까지 시간 체크
        # 시간이 00:00 남으면 종료
        # driver.switch_to.frame(0)
        # body > div.MuiDialog - root > div.MuiDialog - container.MuiDialog - scrollPaper > div > div.MuiDialogActions-root.MuiDialogActions-spacing>button
        driver.execute_script('window.scrollTo(0, 150)')
        while len(driver.find_elements(By.CSS_SELECTOR, "span.fp-remaining")) == 0 \
                or driver.find_element(By.CSS_SELECTOR, "span.fp-remaining").get_attribute("innerHTML") != '00:00':
            time.sleep(5)
        time.sleep(5)
        # driver.switch_to.default_content()

    # Card 진행 - 문서 페이지
    def run_documents(self, driver, p_page_url):
        logging.info(f'Run Documents: {p_page_url}')
        time.sleep(3)
        driver.get(p_page_url)
        time.sleep(3)
        driver.execute_script('window.scrollTo(0, 150)')
        document_completed = False

        # 만약 팝업창이 뜰 경우 자동 클릭
        self._check_popup()

        while not document_completed:
            driver.find_element(By.CSS_SELECTOR, "div.pdf-control > div.pagination > a.pdf-next").click()
            time.sleep(1)
            progress = driver.find_element(By.CSS_SELECTOR, "div.pdf-control > div.pdf-bar > span").get_attribute('style')
            if progress == 'width: 100%;':
                document_completed = True


    # Card 진행 - 서베이 페이지
    def run_survey(self, driver, p_page_url):
        logging.info(f'Run Survey: {p_page_url}')
        time.sleep(3)
        driver.get(p_page_url)
        time.sleep(3)
        grade = self.parent.grade
        reviewText = self.parent.reviewText

        # 평점을 체크한다.
        grade
        self.driver.execute_script("document.querySelectorAll('div.ui.radio.checkbox.iconRadio > input[value="
                                   + grade + "]').forEach(function (el) {el.click();});")
        # 평가기록을 남긴다.
        driver.find_element(By.CSS_SELECTOR, "div.rev-edit > div.edit-wrapper > textarea").send_keys(reviewText)
        driver.find_element(By.CSS_SELECTOR, "div.survey-preview > button.ui.button.fix.bg").click()

        time.sleep(1)

        driver.find_element(By.CSS_SELECTOR, "div.actions.normal.twin > button").click()

    def _check_popup(self):
        # 만약 팝업창이 뜰 경우 자동으로 닫는다.
        self.driver.execute_script("""
            if (document.querySelectorAll('.modal.visible button').length == 1) document.querySelector('.modal.visible button').click()
                """)
        time.sleep(1)

    def _check_finish(self):
        logging.info('MySuni 자동실행기: 지원하지 않는 강의유형입니다. 직접 강의를 수강해주세요. 수강이 완료되면 자동으로 다음 강의로 넘어갑니다.')
        while self.driver.execute_script('return document.querySelector(\'.btn-state-course.act-on\').querySelectorAll(\'.complete\').length == 0'):
            time.sleep(5)
        time.sleep(3)



    # 사용자에게 알리기 위한 헤더 추가
    # 불필요한 오류를 지속적으로 발생시켜 제거함. 모양도 안이쁨
    # def prependHeader(self, driver):
    #     if len(driver.find_elements(By.CSS_SELECTOR,'div#iamsuni')) == 0:
    #         driver.execute_script("""iamsuni_header = document.createElement('div');
    #                                 iamsuni_header.setAttribute('id','iamsuni');
    #                                 iamsuni_header.setAttribute('class','c_badge');
    #                                 iamsuni_header.setAttribute('style','background-color:#EF6D47;font-size:12px;font-weight:bold;height:18px');
    #                                 iamsuni_header.innerHTML = 'MYSuni Player Enabled - Badge Auto Play'
    #                                 iamsuni_header2 = document.createElement('div');
    #                                 iamsuni_header2.setAttribute('style','background-color:#AD482A;height:2px');
    #                                 document.body.prepend(iamsuni_header2);
    #                                 document.body.prepend(iamsuni_header);""")


# 클라이언트에서 구현
# 종료 알림 팝업
# def popup_finish():
#     # This code is to hide the main tkinter window
#     root = tkinter.Tk()
#     root.withdraw()
#
#     # Message Box
#     messagebox.showinfo("종료알림", "강의 수강이 완료되었습니다.")
