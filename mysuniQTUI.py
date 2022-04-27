import sys
import time
import logging
import logging.config

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

from PyQt5.QtWidgets import *
from PyQt5 import uic

from cryptography.fernet import Fernet
import pickle

import mysuniWorker
import mysuniQTPopup

mysuni_ui_class = uic.loadUiType("qt_view_v2_src.ui")[0]
mysuni_popup_class = uic.loadUiType("qt_view_popup.ui")[0]

logging.basicConfig(
  format  = '%(asctime)s:%(levelname)s:%(message)s',
  datefmt = '%I:%M:%S',
  level   = logging.INFO
)

class LogStringHandler(logging.Handler, QObject):
    logSignal = pyqtSignal(int,str)

    def __init__(self):
        super(LogStringHandler, self).__init__()
        QObject.__init__(self)

    def emit(self, record):
        # 잡로그는 무시
        if record.name == 'root':
            self.logSignal.emit(1,record.asctime + ' -- ' + record.getMessage())

class MysuniRunnerWindow(QMainWindow, mysuni_ui_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.grade = '5'
        self.reviewText = '감사합니다.'

        # 키 아무거나.
        self.cipher_suite = Fernet(b'_bOANTWUHxxeJ5cIsksHLaaU4tt0jXXzTYtbP656a2U=')
        self.start_time = time.time()

        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        self.logStringHandler = LogStringHandler()
        logger.addHandler(self.logStringHandler)

        # 이벤트 연결
        self.pb_startMySuni.clicked.connect(self.clicked_mysuni_button)
        self.logStringHandler.logSignal.connect(self.append_log)

        self.m_Survey.triggered.connect(self.clicked_menu_option)

        self.get_identification()

        self.tb_log.append('Badge Mode 는 도전중 Badge를 자동으로 실행합니다.')
        self.tb_log.append('Card Mode 는 Card 에 진입하는 시점부터 자동 실행이 시작됩니다.')
        self.tb_log.append('MySuni 시작 버튼을 클릭하면 세팅이 저장됩니다. (비밀번호는 암호화되어 저장)')
        self.tb_log.append('창을 최소화할 경우 일부 기능이 정상적으로 작동하지 않을 수 있습니다.')
        self.tb_log.append('2022.04.20')
        self.tb_log.append('')

    def clicked_menu_option(self):
        popup = mysuniQTPopup.MysuniPopupWindow()
        popup.getResult(self.grade, self.reviewText)
        if popup.exec():
            self.grade = popup.gradeVal
            self.reviewText = popup.le_review.text()
            logging.info('--- 리뷰설정 ---')
            logging.info('평점:' + self.grade)
            logging.info('강의후기:' + self.reviewText)
        else:
            pass

    def clicked_mysuni_button(self):
        self.set_identification()
        th1 = mysuniWorker.MySuniWorker(self)
        th1.start()

    @pyqtSlot(int, str)
    def append_log(self, i, logTxt):
        self.tb_log.append(logTxt)

    def get_identification(self):
        try:
            with open('my_options.suni', 'rb') as file:
                self.suni_options = pickle.load(file)

            decryptedId = str(self.cipher_suite.decrypt(self.suni_options['id']),'utf-8')
            decryptedPassword = str(self.cipher_suite.decrypt(self.suni_options['pw']),'utf-8')

            self.le_id.setText(decryptedId)
            self.le_pw.setText(decryptedPassword)
            if self.suni_options['card']:
                self.rb_card.setChecked(True)
            else:
                self.rb_badge.setChecked(True)
            self.cb_autodocument.setChecked(self.suni_options['autodoc'])
            self.cb_autosurvey.setChecked(self.suni_options['autosurvey'])
            self.dsb_videospeed.setValue(float(self.suni_options['videospeed']))
            self.sb_hourlimit.setValue(int(self.suni_options['maxhour']))
            self.grade = self.suni_options['grade']
            self.reviewText = self.suni_options['reviewText']

        except BaseException as e:
            print(e)

    # id, pw, card/badge, autodoc, autosurvey, videospeed, maxhour
    def set_identification(self):
        try:
            encryptedId = ''
            encryptedPassword = ''
            if len(self.le_id.text()) > 0:
                encryptedId = self.cipher_suite.encrypt(bytes(self.le_id.text(),'utf-8'))
            if len(self.le_pw.text()) > 0:
                encryptedPassword = self.cipher_suite.encrypt(bytes(self.le_pw.text(),'utf-8'))
            self.suni_options = {'id': encryptedId,
                                 'pw': encryptedPassword,
                                 'card' : self.rb_card.isChecked(),
                                 'autodoc' : self.cb_autodocument.isChecked(),
                                 'autosurvey' : self.cb_autosurvey.isChecked(),
                                 'videospeed' : self.dsb_videospeed.text(),
                                 'maxhour' : self.sb_hourlimit.text(),
                                 'grade' : self.grade,
                                 'reviewText' : self.reviewText}
            with open('my_options.suni', 'wb') as file:
                pickle.dump(self.suni_options, file)
        except BaseException as e:
            print(e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mysuni_window = MysuniRunnerWindow()
    mysuni_window.show()
    app.exec_()