from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from time import sleep
from datetime import datetime

# 不同窗口显示的位置不同
geos = [200, 500, 800]

class window(QMainWindow):
	'''
	窗口
	'''
	def __init__(self, num):
		super().__init__()
		self.num = int(num) # 窗口编号
		self.initUI()

	def initUI(self):
		self.setFont(QFont('Arial',14))

		window_name = '窗口' + str(self.num)
		self.setWindowTitle(window_name)

		ind = self.num - 1
		self.setGeometry(geos[ind], geos[ind], 400, 200)
		self.setFixedSize(self.width(), self.height())

		self.lb = QLabel(self)
		self.lb.setGeometry(100,50,200,100)
		self.lb.setAlignment(Qt.AlignCenter)

	def progress_1(self, T):
		for i in range(T):
			dt = datetime.now()
			contents = dt.strftime('%Y-%m-%d %H:%M:%S')
			self.lb.setText(contents)
			QApplication.processEvents()
			sleep(1)

	def progress_2(self, T):
		num = 0
		for i in range(T):
			self.lb.setText(str(num))
			if num < 9:
				num = num + 1
			else:
				num = 0
			QApplication.processEvents()
			sleep(1)

	def progress_3(self, T):
		sum_ = 0
		add_ = 0
		for i in range(T):
			sum_ = sum_ + add_
			add_ = add_ + 1
			contents = 'For 0 to {}, sum is {}'.format(add_-1, sum_)
			self.lb.setText(contents)
			QApplication.processEvents()
			sleep(1)
			if add_ == 1001: # 超过1k后将不再累加
				break

app = QApplication(sys.argv)
num = sys.argv[1]

w = window(num)
w.show()
sleep(3)

# 不同进程对应不同操作

T = 10 # 周期
if w.num == 1:
	w.progress_1(T)
elif w.num == 2:
	w.progress_2(T)
elif w.num == 3:
	w.progress_3(T)

w.close()
sys.exit(app.exec_())