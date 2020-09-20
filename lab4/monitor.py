from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import os
import sys
import time, datetime
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns

QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # 设置支持高分辨率屏幕自适应
sns.set() # seaborn美化

class ClickedLabel(QLabel):
	'''
	实现可点击的QLabel类
	'''
	clicked = pyqtSignal()

	def mouseReleaseEvent(self, QMouseEvent):
		if QMouseEvent.button() == Qt.LeftButton:
			self.clicked.emit()

class Thread_Read(threading.Thread):
	'''
	读线程
	'''
	def __init__(self):
		super().__init__()
		self.timer = QTimer(monitor)
		self.timer.timeout.connect(self.run)
		self.timer.start(1000 * monitor.T)

	def run(self):

		# 时间
		lock_time_empty.acquire()
		#s1 = time.time()
		now_time = datetime.datetime.now()
		buf[0] = datetime.datetime.strftime(now_time, '%Y-%m-%d\n%H:%M:%S')
		#s2 = time.time()
		#print('Time READ : ' + str(s2-s1))
		lock_time_full.release()

		# CPU MHz
		lock_mhz_empty.acquire()
		#s1 = time.time()
		try:
			f = open('/proc/cpuinfo')
			while True:
				line = f.readline()
				if line.startswith('cpu MHz'):
					buf[1] = line.split(':')[1].strip()
					break

			f.close()
		except:
			pass
		#s2 = time.time()
		#print('CPU MHZ READ : ' + str(s2-s1))
		lock_mhz_full.release()

		# CPU Usage
		lock_cpu_empty.acquire()
		#s1 = time.time()
		try:
			f = os.popen('vmstat -w -w')
			contents = f.read()
			buf[2] = 100 - int(contents.split()[-3])
		except:
			pass
		#s2 = time.time()
		#print('CPU Usage READ : ' + str(s2-s1))
		lock_cpu_full.release()

		# Memory Usage & Swap Usage
		lock_mem_empty.acquire()
		lock_swap_empty.acquire()
		#s1 = time.time()
		try:
			f = open('/proc/meminfo')
			MemTotal = ''
			MemAvailable = ''
			SwapTotal = ''
			SwapFree = ''

			while True: # 提取信息
				line = f.readline()
				if not line:
					break
				if line.startswith('MemTotal'):
					MemTotal = line.split(':')[1].strip()
				if line.startswith('MemAvailable'):
					MemAvailable = line.split(':')[1].strip()
				if line.startswith('SwapTotal'):
					SwapTotal = line.split(':')[1].strip()
				if line.startswith('SwapFree'):
					SwapFree = line.split(':')[1].strip()

			buf[3] = (1 - int(MemAvailable[:-3]) / int(MemTotal[:-3])) * 100
			buf[4] = (1 - int(SwapFree[:-3]) / int(SwapTotal[:-3])) * 100

			f.close()
		except:
			pass

		#s2 = time.time()
		#print('Mem + Swap READ : ' + str(s2-s1))
		lock_mem_full.release()
		lock_swap_full.release()

class Thread_Read_Process(threading.Thread):
	'''
	读线程(进程)
	'''
	def __init__(self):
		super().__init__()
		self.timer = QTimer(monitor)
		self.timer.timeout.connect(self.run)
		self.timer.start(1000 * monitor.T)

	def run(self):

		# 进程
		lock_process_empty.acquire()
		#s1 = time.time()
		try:
			dirs = os.listdir('/proc')
			pids = list(filter(lambda x: os.path.isdir('/proc/' + x) and x.isdigit(), dirs))

			buf_process['pids_num'] = len(pids)

			# 提取进程信息
			for index, pid in enumerate(pids):
				contents = []
				try:
					f1 = open('/proc/' + pid + '/stat')
					f2 = open('/proc/' + pid + '/statm')
					if f1:
						content = f1.read().split()
						contents += [content[0], content[1][1:-1], content[2]] # 进程号，进程名，进程状态
						f1.close()
					if f2:
						content = f2.read().split()
						contents += [content[1]] # 实际内存
						f2.close()
				except:
					buf_process['pids_num'] = buf_process['pids_num'] - 1 # 异常判断
					continue

				buf_process[str(index)] = contents
		except:
			pass
		#s2 = time.time()
		#print('Process READ : ' + str(s2-s1))
		lock_process_full.release()

class Thread_Write(threading.Thread):
	'''
	定时写线程
	'''
	def __init__(self):
		super().__init__()

		# 用于动态折线图中
		self.time_buf = []
		self.cpu_usage_buf = []
		self.mem_usage_buf = []
		self.swap_usage_buf = []

		# 已开始时间
		self.start_time = 0

	def run(self):

		while True:

			# 时间
			lock_time_full.acquire()
			#s1 = time.time()
			monitor.lb_time.setText(buf[0])
			#s2 = time.time()
			#print('Time WRITE : ' + str(s2-s1))
			lock_time_empty.release()

			# CPU MHz
			lock_mhz_full.acquire()
			#s1 = time.time()
			monitor.tb1.setItem(3, 0, QTableWidgetItem(buf[1]))
			#s2 = time.time()
			#print('CPU MHZ WRITE : ' + str(s2-s1))
			lock_mhz_empty.release()

			# CPU Usage
			lock_cpu_full.acquire()
			#s1 = time.time()
			monitor.bar1.setValue(buf[2])

			plt.clf()  # 重新作图
			plt.subplot(231)
			new_x = [buf[2], 100-buf[2]]
			plt.pie(new_x, labels=['Use', 'Not Use'], autopct='%.1f%%')
			plt.title('CPU Usage')

			plt.subplot(234)
			plt.xlabel('t/s')
			plt.xlim(0,30)
			plt.ylim(0,100)

			if self.start_time <= 30:
				self.time_buf.append(self.start_time) # 时间序列++
				self.cpu_usage_buf.append(buf[2])
			else:
				self.time_buf = self.time_buf[1:] + [self.start_time]
				plt.xlim(self.time_buf[0], self.time_buf[-1])
				self.cpu_usage_buf = self.cpu_usage_buf[1:] + [buf[2]]

			plt.plot(self.time_buf, self.cpu_usage_buf)
			plt.title('CPU Usage')
			#s2 = time.time()
			#print('CPU Usage WRITE : ' + str(s2-s1))
			lock_cpu_empty.release()

			# Memory Usage
			lock_mem_full.acquire()
			#s1 = time.time()
			monitor.bar2.setValue(buf[3])

			plt.subplot(232)
			new_x = [buf[3], 100-buf[3]]
			plt.pie(new_x, labels=['Use', 'Not Use'], autopct='%.1f%%')
			plt.title('Memory Usage')

			plt.subplot(235)
			plt.xlabel('t/s')
			plt.xlim(0,30)
			plt.ylim(0,100)

			if self.start_time <= 30:
				self.mem_usage_buf.append(buf[3])
			else:
				plt.xlim(self.time_buf[0], self.time_buf[-1])
				self.mem_usage_buf = self.mem_usage_buf[1:] + [buf[3]]

			plt.plot(self.time_buf, self.mem_usage_buf)
			plt.title('Memory Usage')
			#s2 = time.time()
			#print('Mem WRITE : ' + str(s2-s1))

			lock_mem_empty.release()

			# Swap Usage
			lock_swap_full.acquire()
			#s1 = time.time()
			monitor.bar3.setValue(buf[4])

			plt.subplot(233)
			new_x = [buf[4], 100-buf[4]]
			plt.pie(new_x, labels=['Use', 'Not Use'], autopct='%.1f%%')
			plt.title('Swap Usage')

			plt.subplot(236)
			plt.xlabel('t/s')
			plt.xlim(0,30)
			plt.ylim(0,100)

			if self.start_time <= 30:
				self.swap_usage_buf.append(buf[4])
			else:
				plt.xlim(self.time_buf[0], self.time_buf[-1])
				self.swap_usage_buf = self.swap_usage_buf[1:] + [buf[4]]

			plt.plot(self.time_buf, self.swap_usage_buf)
			plt.title('Swap Usage')

			self.start_time = self.start_time + monitor.T # 计时器+周期T
			monitor.canvas.draw() # 重新绘制

			#s2 = time.time()
			#print('Swap + Draw WRITE : ' + str(s2-s1))
			lock_swap_empty.release()

			# Process
			lock_process_full.acquire()
			#s1 = time.time()
			pids_num = buf_process['pids_num']
			monitor.tb2_w.setRowCount(pids_num)

			for key in buf_process.keys():
				if key == 'pids_num':
					continue
				contents = buf_process[key]
				for j in range(4):
					monitor.tb2_w.setItem(int(key), j, QTableWidgetItem(contents[j]))

			#s2 = time.time()
			#print('Process WRITE : ' + str(s2-s1) + '\n')
			lock_process_empty.release()

			QApplication.processEvents() # 刷新页面，防止锁死

class system_monitor(QMainWindow):
	'''
	系统监控器
	'''
	def __init__(self):
		super().__init__()
		self.upper_dir = '/home/yingjia' # 根目录
		self.now_dir = '/home/yingjia' # 用于在后续文件系统中确定目录

		self.dir_prefix = '<DIR>: ' # 输出栏当前目录的前缀
		self.message_prefix = '<MESSAGE>: ' # 输出栏提示消息的前缀

		self.T = 1 # 刷新周期

		self.initUI() # 初始化界面

		self.update_OverView() # 更新总览
		self.update_processes() # 更新进程
		self.update_files() # 更新文件
		self.update_charts() # 更新图表

	def initUI(self):
		'''
		初始化界面
		'''
		self.setFont(QFont("Arial",12))
		self.setGeometry(200,100,1000,800)
		self.setFixedSize(self.width(), self.height())
		self.setWindowTitle('System Monitor')

		self.initMenu() # 初始化菜单栏
		self.initTab() # 初始化网格
		self.initWidgets() # 初始化其他控件

	def initMenu(self):
		'''
		初始化菜单栏
		'''

		# 菜单栏-功能
		self.menubar = self.menuBar()
		self.menu = self.menubar.addMenu('Functions')

		self.ac1 = QAction('[Files] Total Memory', self) # 计算该目录内存总占用
		self.ac1.setShortcut('Ctrl+M')
		self.ac1.triggered.connect(self.total_memory)

		self.ac2 = QAction('[Files] To Upper', self) # 返回上一层
		self.ac2.setShortcut('Ctrl+U')
		self.ac2.setEnabled(False) # 默认为根目录，不可用
		self.ac2.triggered.connect(self.to_upper)

		self.ac3 = QAction('Change Refresh Cycle', self) # 改变刷新周期
		self.ac3.setShortcut('Ctrl+C')
		self.ac3.triggered.connect(self.change_refresh_cycle)

		self.ac4 = QAction('Quit', self) # 退出
		self.ac4.setShortcut('Ctrl+Q')
		self.ac4.triggered.connect(qApp.quit)

		self.ac5 = QAction('[Process] Find', self) # 查找进程
		self.ac5.setShortcut('Ctrl+F')
		self.ac5.triggered.connect(self.find_process)

		self.ac6 = QAction('[Process] Kill', self) # 杀死进程
		self.ac6.setShortcut('Ctrl+K')
		self.ac6.triggered.connect(self.kill)

		self.ac7 = QAction('Stop Refresh', self) # 暂停刷新
		self.ac7.setShortcut('Ctrl+S')
		self.ac7.triggered.connect(self.stop_refresh)

		self.ac8 = QAction('[Files] Find', self) # 查找文件
		self.ac8.setShortcut('Ctrl+G')
		self.ac8.triggered.connect(self.find_files)

		# 依次添加进入菜单
		self.menu.addAction(self.ac3)
		self.menu.addAction(self.ac7)
		self.menu.addAction(self.ac5)
		self.menu.addAction(self.ac6)
		self.menu.addAction(self.ac8)
		self.menu.addAction(self.ac1)
		self.menu.addAction(self.ac2)
		self.menu.addAction(self.ac4)

		# 菜单栏-关于
		self.menubar_about = self.menuBar()
		self.menu_about = self.menubar_about.addMenu('About')

		self.ac_about = QAction('About', self)
		self.ac_about.triggered.connect(self.about)

		self.menu_about.addAction(self.ac_about)

	def initTab(self):
		'''
		初始化网格
		'''
		self.tb = QTabWidget(self)
		self.tb.setGeometry(0,30,1000,640)

		# 总览
		self.tb1 = QTableWidget()

		tb1_vertical_header_labels = ['Hostname', 'System Version', 'CPU ', 'CPU MHz']
		self.tb1.setRowCount(len(tb1_vertical_header_labels))
		self.tb1.setColumnCount(1)
		self.tb1.setHorizontalHeaderLabels(['Info'])
		self.tb1.setVerticalHeaderLabels(tb1_vertical_header_labels)
		self.tb1.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不允许用户编辑
		self.tb1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # 设置水平方向为表格自适应的伸缩模式

		# 进程
		self.tb2 = QWidget()
		self.tb2_grid = QGridLayout()
		self.tb2.setLayout(self.tb2_grid)

		self.le1 = QLineEdit()
		self.le1.setPlaceholderText('Please input PID here.')
		self.tb2_w = QTableWidget()

		# 进程中布局
		self.tb2_grid.addWidget(self.le1, 1, 0)
		self.tb2_grid.addWidget(self.tb2_w, 2, 0, 10, 0)
		
		tb2_horizontal_header_labels = ['PID', 'NAME', 'STAT', 'MEMORY']
		self.tb2_w.setColumnCount(len(tb2_horizontal_header_labels))
		self.tb2_w.setHorizontalHeaderLabels(tb2_horizontal_header_labels)
		self.tb2_w.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不允许用户编辑
		self.tb2_w.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)# 设置水平方向为表格自适应的伸缩模式3
		self.tb2_w.setSelectionBehavior(QAbstractItemView.SelectRows) # 设置表格整行选中

		# 文件
		self.tb3 = QWidget()
		self.tb3_grid = QGridLayout()
		self.tb3.setLayout(self.tb3_grid)

		self.le2 = QLineEdit()
		self.le2.setPlaceholderText('Please input name here.')
		self.tb3_w = QTableWidget()

		# 文件中布局
		self.tb3_grid.addWidget(self.le2, 1, 0)
		self.tb3_grid.addWidget(self.tb3_w, 2, 0, 10, 0)

		tb3_horizontal_header_labels = ['size', 'name', 'is_dir']
		self.tb3_w.setColumnCount(len(tb3_horizontal_header_labels))
		self.tb3_w.setHorizontalHeaderLabels(tb3_horizontal_header_labels)
		self.tb3_w.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不允许用户编辑
		self.tb3_w.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # 设置水平方向为表格自适应的伸缩模式
		self.tb3_w.setSelectionBehavior(QAbstractItemView.SelectRows) # 设置表格整行选中
		self.tb3_w.itemDoubleClicked.connect(self.to_new_files) # 双击触发事件

		# 图表
		self.tb4 = QWidget()

		# 依次添加进网格
		self.tb.addTab(self.tb1, "OverView")
		self.tb.addTab(self.tb2, "Process")
		self.tb.addTab(self.tb3, "Files")
		self.tb.addTab(self.tb4, "Resources")

	def initWidgets(self):
		'''
		初始化其他控件
		'''

		# 系统时间
		self.lb_time = QLabel(self)
		self.lb_time.setGeometry(10,695,80,80)
		self.lb_time.setAlignment(Qt.AlignCenter)

		# CPU使用率
		self.lb1 = QLabel(self)
		self.lb1.setGeometry(100,685,120,20)
		self.lb1.setAlignment(Qt.AlignCenter)
		self.lb1.setText('CPU Usage: ')

		self.bar1 = QProgressBar(self)
		self.bar1.setGeometry(220,680,120,30)

		# 内存使用率
		self.lb2 = QLabel(self)
		self.lb2.setGeometry(100,725,120,20)
		self.lb2.setAlignment(Qt.AlignCenter)
		self.lb2.setText('Memory Usage: ')

		self.bar2 = QProgressBar(self)
		self.bar2.setGeometry(220,720,120,30)

		# 交换分区使用率
		self.lb3 = QLabel(self)
		self.lb3.setGeometry(100,765,120,20)
		self.lb3.setAlignment(Qt.AlignCenter)
		self.lb3.setText('Swap Usage: ')

		self.bar3= QProgressBar(self)
		self.bar3.setGeometry(220,760,120,30)

		# 关机
		pic = QPixmap('shutdown.jpg')
		self.lb4 = ClickedLabel(self) # 使用自定义Label类
		self.lb4.setGeometry(900,690,90,90)
		self.lb4.setScaledContents(True) # 缩放
		self.lb4.setPixmap(pic)
		self.lb4.clicked.connect(self.shutdown)

		# 输出栏-上
		self.op1 = QLabel(self)
		self.op1.setGeometry(350,700,540,25)
		self.op1.setAlignment(Qt.AlignLeft)

		# 输出栏-下
		self.op2 = QLabel(self)
		self.op2.setGeometry(350,750,540,25)
		self.op2.setAlignment(Qt.AlignLeft)

	def update_OverView(self):
		'''
		更新总览
		'''

		# 时间
		now_time = datetime.datetime.now()
		now_time = datetime.datetime.strftime(now_time, '%Y-%m-%d\n%H:%M:%S')
		self.lb_time.setText(now_time)

		# hostname
		hostname = os.popen('cat /proc/sys/kernel/hostname').read().strip()
		self.tb1.setItem(0, 0, QTableWidgetItem(hostname))

		# system version
		system_version = os.popen('cat /proc/sys/kernel/ostype').read().strip() + ' '
		system_version += os.popen('cat /proc/sys/kernel/osrelease').read().strip()
		self.tb1.setItem(1, 0, QTableWidgetItem(system_version))

		# CPU & CPU MHz
		f = open('/proc/cpuinfo')
		ok = 2
		cpu = ''
		cpu_MHz = ''

		while True:
			line = f.readline()
			if not line:
				break
			if line.startswith('model name'):
				cpu = line.split(':')[1].strip()
				ok = ok - 1
			if line.startswith('cpu MHz'):
				cpu_MHz = line.split(':')[1].strip()
				ok = ok - 1
			if not ok:
				break

		f.close()
		self.tb1.setItem(2, 0, QTableWidgetItem(cpu))
		self.tb1.setItem(3, 0, QTableWidgetItem(cpu_MHz))

		# CPU Usage
		f = os.popen('vmstat -w -w').read()
		cpu_usage = 100 - int(f.split()[-3])

		self.bar1.setValue(cpu_usage)

		# Memory Usage & Swap Usage
		f = open('/proc/meminfo')
		MemTotal = ''
		MemAvailable = ''
		SwapTotal = ''
		SwapFree = ''

		while True: # 提取信息
			line = f.readline()
			if not line:
				break
			if line.startswith('MemTotal'):
				MemTotal = line.split(':')[1].strip()
			if line.startswith('MemAvailable'):
				MemAvailable = line.split(':')[1].strip()
			if line.startswith('SwapTotal'):
				SwapTotal = line.split(':')[1].strip()
			if line.startswith('SwapFree'):
				SwapFree = line.split(':')[1].strip()

		f.close()

		memory_usage = (1 - int(MemAvailable[:-3]) / int(MemTotal[:-3])) * 100
		swap_usage = (1 - int(SwapFree[:-3]) / int(SwapTotal[:-3])) * 100
		
		self.bar2.setValue(memory_usage)
		self.bar3.setValue(swap_usage)

	def update_processes(self):
		'''
		更新进程
		'''

		# 获得全部进程号
		dirs = os.listdir('/proc')
		pids = list(filter(lambda x: os.path.isdir('/proc/' + x) and x.isdigit(), dirs))

		self.tb2_w.setRowCount(len(pids))

		# 提取进程信息
		for index, pid in enumerate(pids):
			contents = []
			try: # 异常判断
				f = open('/proc/' + pid + '/stat')
				content = f.read().split()
				contents += [content[0], content[1][1:][:-1], content[2]] # 进程号，进程名，进程状态
				f.close()
			except:
				continue
			
			try:
				f = open('/proc/' + pid + '/statm')
				content = f.read().split()
				contents += [content[1]] # 实际内存
				f.close()
			except:
				continue

			for i in range(4):
				self.tb2_w.setItem(index-1, i, QTableWidgetItem(contents[i]))

	def update_files(self):
		'''
		更新文件管理
		'''
		if self.now_dir != self.upper_dir:
			self.ac2.setEnabled(True) # 如果不是根目录，将上一层按钮变为可用状态

		f = os.popen('du -sh ' + self.now_dir + '/*').read()
		files = f.split('\n')[:-1]
		
		self.tb3_w.setRowCount(len(files)) # 确定文件及文件夹数目

		for index, file in enumerate(files):
			size, name = file.split('\t')
			self.tb3_w.setItem(index, 0, QTableWidgetItem(size))
			self.tb3_w.setItem(index, 1, QTableWidgetItem(name.replace(self.now_dir+'/', '')))

			isdir_flag = ''
			if os.path.isdir(name): # 记录是否为目录
				isdir_flag = 'Y'
			else:
				isdir_flag = 'N'
		
			self.tb3_w.setItem(index, 2, QTableWidgetItem(isdir_flag))

		self.op1.setText(self.dir_prefix + self.now_dir) # 使用输出栏1

	def update_charts(self):
		'''
		更新图表
		'''

		# 创建作图区
		self.figure = plt.figure()
		self.canvas = FigureCanvas(self.figure)

		self.vbox = QVBoxLayout()
		self.tb4.setLayout(self.vbox)
		self.vbox.addWidget(self.canvas)

		# CPU Usage
		cpu_usage = self.bar1.value()
		plt.subplot(231)
		x = [cpu_usage, 100 - cpu_usage]
		plt.pie(x, labels=['Use', 'Not Use'], autopct='%.1f%%')
		plt.title('CPU Usage')

		# Memory Usage
		mem_usage = self.bar2.value()
		plt.subplot(232)
		x = [mem_usage, 100 - mem_usage]
		plt.pie(x, labels=['Use', 'Not Use'], autopct='%.1f%%')
		plt.title('Memory Usage')

		# Swap Usage
		swap_usage = self.bar3.value()
		plt.subplot(233)
		x = [swap_usage, 100 - swap_usage]
		plt.pie(x, labels=['Use', 'Not Use'], autopct='%.1f%%')
		plt.title('Swap Usage')

		self.canvas.draw()

	def change_refresh_cycle(self):
		'''
		改变刷新周期
		'''
		limit = [str(i) for i in range(1,11)]
		T, ok = QInputDialog.getItem(self, 'Message', 'Please change the refresh cycle.', limit)
		if T not in limit:
			QMessageBox.warning(self,'Alert','Input is not available!',QMessageBox.Ok)			
		else:
			self.T = int(T)
			thread_r.timer.stop()
			thread_rp.timer.stop()
			thread_r.timer.start(1000 * self.T)
			thread_rp.timer.start(1000 * self.T)

	def stop_refresh(self):
		'''
		停止刷新
		'''
		thread_r.timer.stop()
		thread_rp.timer.stop()

	def to_new_files(self):
		'''
		触发打开文件夹/文件
		'''
		index = self.tb3_w.currentIndex().row()
		isdir_flag = self.tb3_w.item(index, 2).text()

		if isdir_flag == 'Y': # 判断是否为目录
			self.now_dir = self.now_dir + '/' + self.tb3_w.item(index, 1).text()
			self.update_files() # 更新文件目录
		else: # 打开文件
			os.system("xdg-open " + self.now_dir + '/' + self.tb3_w.item(index, 1).text()) # 打开文件

	def find_process(self):
		'''
		查找进程
		'''
		text = self.le1.text().strip() 
		items = self.tb2_w.findItems(text, Qt.MatchExactly)
		if items:
			items[0].setSelected(True)
			self.tb2_w.verticalScrollBar().setSliderPosition(items[0].row())
			self.op2.setText(self.message_prefix + 'Find Successfully!')
		else:
			self.op2.setText(self.message_prefix + 'No such process.')

	def find_files(self):
		'''
		查找文件
		'''
		text = self.le2.text().strip() 
		items = self.tb3_w.findItems(text, Qt.MatchExactly)
		if items:
			items[0].setSelected(True)
			self.tb3_w.verticalScrollBar().setSliderPosition(items[0].row())
			self.op2.setText(self.message_prefix + 'Find Successfully!')
		else:
			self.op2.setText(self.message_prefix + 'No such files.')

	def kill(self):
		'''
		杀死进程
		'''
		text = self.le1.text().strip()
		items = self.tb2_w.findItems(text, Qt.MatchExactly)
		if items:
			ans = os.system('kill -9 ' + text)
			if ans == 0:
				self.op2.setText(self.message_prefix + 'Kill Successfully!')
			else:
				self.op2.setText(self.message_prefix + 'Error.')
		else:
			self.op2.setText(self.message_prefix + 'No such process.')

	def total_memory(self):
		'''
		返回上一层获得内存总占用
		'''
		rsplit_parts = self.now_dir.rsplit('/', 1)
		new_dir, dir_name = rsplit_parts[0], rsplit_parts[1]

		f = os.popen('du -sh ' + new_dir + '/*').read()
		files = f.split('\n')[:-1]

		for index, file in enumerate(files):
			size, name = file.split('\t')
			new_name = name.replace(new_dir+'/', '')
			if new_name == dir_name:
				self.op2.setText(self.message_prefix + 'Total Memory : ' + size) # 使用输出栏2
				break

	def to_upper(self):
		'''
		上一层
		'''
		if self.now_dir != self.upper_dir: #当现目录不是根目录
			self.now_dir = self.now_dir.rsplit('/', 1)[0]
			
			if self.now_dir == self.upper_dir:
				self.ac2.setEnabled(False) # 当上一层为根目录时，该按钮将不可用
			self.update_files()

	def shutdown(self):
		'''
		关机
		'''
		reply = QMessageBox.information(self, 'Message', 'Do you really want to shut the system down?', QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
		if reply == QMessageBox.Yes:
			QMessageBox.information(self, 'Message', 'System will be shut down in 2s.', QMessageBox.Ok)
			time.sleep(2)
			os.system('shutdown -h now')

	def about(self):
		'''
		关于
		'''
		message = 'Made by YingjiaWang from HUST\n' + \
			'Instructed By Prof. Ke Shi'
		QMessageBox.information(self, 'Message', message, QMessageBox.Ok)

if __name__ == '__main__':

	app = QApplication(sys.argv)
	monitor = system_monitor()
	monitor.show()
	
	# 创建缓冲区
	buf = [
		monitor.lb_time.text(), 
		monitor.tb1.item(3,0).text(), 
		monitor.bar1.value(),
		monitor.bar2.value(),
		monitor.bar3.value()
		]

	buf_process = {}

	# 创建锁
	lock_time_empty = threading.Semaphore(1)
	lock_time_full = threading.Semaphore(0)

	lock_mhz_empty = threading.Semaphore(1)
	lock_mhz_full = threading.Semaphore(0)

	lock_cpu_empty = threading.Semaphore(1)
	lock_cpu_full = threading.Semaphore(0)

	lock_mem_empty = threading.Semaphore(1)
	lock_mem_full = threading.Semaphore(0)

	lock_swap_empty = threading.Semaphore(1)
	lock_swap_full = threading.Semaphore(0)

	lock_process_empty = threading.Semaphore(1)
	lock_process_full = threading.Semaphore(0)

	# 创建读写线程，读线程中进程信息的读取单独作为另一个线程处理
	thread_r = Thread_Read()
	thread_rp = Thread_Read_Process()
	thread_w = Thread_Write()

	# 线程开始执行
	thread_r.start()
	thread_rp.start()
	thread_w.start()

	sys.exit(app.exec_())
