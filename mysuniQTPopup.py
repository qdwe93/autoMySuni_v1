from PyQt5.QtWidgets import *
from PyQt5 import uic


mysuni_popup_class = uic.loadUiType("qt_view_popup.ui")[0]


class MysuniPopupWindow(QDialog, mysuni_popup_class):
    # mysuni_popup_class = uic.loadUiType("qt_view_popup.ui")[0]
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.setResult)

    def getResult(self, grade, reviewText):
        self.le_review.setText(reviewText)
        if grade == '1':
            self.rb_point1.setChecked(True)
        elif grade == '2':
            self.rb_point2.setChecked(True)
        elif grade == '3':
            self.rb_point3.setChecked(True)
        elif grade == '4':
            self.rb_point4.setChecked(True)
        elif grade == '5':
            self.rb_point5.setChecked(True)

    def setResult(self):
        if self.rb_point1.isChecked():
            self.gradeVal = self.rb_point1.text()
        elif self.rb_point2.isChecked():
            self.gradeVal = self.rb_point2.text()
        elif self.rb_point3.isChecked():
            self.gradeVal = self.rb_point3.text()
        elif self.rb_point4.isChecked():
            self.gradeVal = self.rb_point4.text()
        elif self.rb_point5.isChecked():
            self.gradeVal = self.rb_point5.text()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     mysuni_popup = MysuniPopupWindow()
#     mysuni_popup.show()
#     app.exec_()
