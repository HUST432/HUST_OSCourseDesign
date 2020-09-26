import os
import datetime
import math
import re
from colorama import Fore, Style
from config import *

def Help():
	'''
	帮助
	'''
	print('Help:')
	print('1.  cd     切换路径')
	print('2.  ls     展示全部文件（夹）')
	print('3.  clear  清空控制台')
	print('4.  mkdir  创建目录')
	print('5.  rmdir  删除目录')
	print('6.  create 创建文件')
	print('7.  rm     删除文件')
	print('8.  read   读文件')
	print('9.  write  写文件')
	print('10. cp     复制文件')
	print('11. mv     移动文件')
	print('12. chmod  更改文件权限(admin/create_user)')
	print('13. aduser 增加用户(admin)')
	print('14. rmuser 删除用户(admin)')
	print('15. lsuser 展示全部用户(admin)')
	print('16. info   显示系统信息')
	print('17  save   保存')
	print('18. logout 注销')
	print('19. exit   退出')
	print('20. help   帮助')

def load(f):
	'''
	读取文件系统信息
	'''

	# 1 superblock
	superblock = f.readline().strip().split()

	# 判断程序中的MEMORY_MAX和BLOCKS_MAX是否兼容该文件系统
	assert MEMORY_MAX == int(superblock[0]), 'Incompatible MEMORY_MAX!'
	assert BLOCKS_MAX == int(superblock[1]), 'Incompatible BLOCKS_MAX!'
	
	# 2 users
	users = f.readline().strip().split()
	user_num = int(len(users)/2)

	for i in range(user_num):
		username = users[2 * i]
		password = users[2 * i + 1]
		user_dict[i] = [username, password]

	# 3 files
	global file_num

	files = f.readline().strip().split()
	file_num = int(len(files)/2) # 更新文件总数

	for i in range(file_num):
		file_id = int(files[2 * i])
		block_id = int(files[2 * i + 1])
		file_indexes[file_id] = block_id

	# 4 access
	access = f.readline().strip().split()
	for i in range(int(len(access)/2)):
		file_id = int(access[2 * i])
		file_access = access[2 * i + 1]
		access_indexes[file_id] = [file_access[0], file_access[1]]

	# 5 BLOCKS
	global blocks, block_indexes, free_blocks
	from config import block

	for _ in range(4):
		b = block()
		b.memory = [' ' for _ in range(MEMORY_MAX)]
		blocks.append(b)

	for _ in range(BLOCKS_MAX-4):
		line = f.readline()[:-1] # 去掉末尾的换行符
		line = line.replace('$', '\n') # 把换行符变回来
		line = list(line) # 转变成list的格式

		# 创建新块
		b = block()
		b.memory = line
		blocks.append(b)

	# 加入块索引词典
	block_indexes = dict(zip([(i+1) for i in range(BLOCKS_MAX)], blocks))

	# 创建空块链表
	free_blocks = list(filter(lambda x: x not in file_indexes.values(), [i for i in range(5, BLOCKS_MAX+1)]))

	# 初始化文件和目录相关项
	global file_dict

	file_dict = {}

	for k, v in file_indexes.items():
		block = block_indexes[int(v)]

		info_string = ''.join(block.memory).strip().split()
		# example file format: ['t', '2', '2020-09-25', '21:28:32', '1', '1', '6', '3']
		# example dir format: ['root', '1', 't']

		now_time = get_time()
		if len(info_string) > 2 and info_string[2].startswith(now_time[:3]): # 文件
			new_file = file(info_string[0], int(info_string[1]), info_string[2]+' '+info_string[3])
			new_file.create_userid = int(info_string[4])
			new_file.index_table_len = int(info_string[5])
			new_file.index_table = int(info_string[6])
			new_file.last_block_len = int(info_string[7])
			file_dict[int(info_string[1])] = new_file # 加入索引

			if new_file.index_table_len > 1: # 存在索引表
				# 把占的块从free_blocks清除，标记为不可用
				decoder = ''.join(block.memory[:4 * file_node.index_table_len]) 
				decoder = re.findall('....', decoder) # 32位解码，每隔4位一切割

				delete_list = [decoder_32(i) for i in decoder] # 索引表中对应的磁盘号
				for i in delete_list:
					free_blocks.remove(i)
				free_blocks.remove(new_file.index_table)
			else: # 不存在索引表
				free_blocks.remove(new_file.index_table)

		else: # 目录
			new_dir = dir(info_string[0], int(info_string[1]))
			new_dir.children = list(map(lambda x: int(x), info_string[2:])) # 将str型ID映射为int型

			file_dict[int(info_string[1])] = new_dir # 加入索引

	# 初始化目录
	global root, current_root
	root = file_dict[1]
	current_root = file_dict[1]

def save():
	'''
	存文件系统信息
	'''
	f = open('filesystem', 'w')

	# 1 superblock
	info_string = list(str(MEMORY_MAX) + ' ' +\
		str(BLOCKS_MAX))

	info_string += [' ' for _ in range(MEMORY_MAX - len(info_string))]
	f.writelines(info_string + ['\n'])
	
	# 2 users
	def func(x):
		return [' '.join(value) for value in list(x.values())]

	info_string = func(user_dict)
	info_string = list(' '.join(info_string))

	info_string += [' ' for _ in range(MEMORY_MAX - len(info_string))]
	f.writelines(info_string + ['\n'])

	# 3 files
	def func(x):
		k, v = list(x.keys()), list(x.values())
		info_string = ''
		for i in range(len(k)):
			info_string += str(k[i]) + ' '
			info_string += str(v[i]) + ' '
		return list(info_string)
	info_string = func(file_indexes)

	info_string += [' ' for _ in range(MEMORY_MAX - len(info_string))]
	f.writelines(info_string + ['\n'])

	# 4 access
	def func(x):
		k, v = list(x.keys()), list(x.values())
		v = [value[0]+value[1] for value in v]
		info_string = ''
		for i in range(len(k)):
			info_string += str(k[i]) + ' '
			info_string += v[i] + ' '
		return list(info_string)

	info_string = func(access_indexes)

	info_string += [' ' for _ in range(MEMORY_MAX - len(info_string))]
	f.writelines(info_string + ['\n'])

	# 5-BLOCKS_MAX
	for i in range(5, BLOCKS_MAX+1):
		block = block_indexes[i]
		block.memory = [c.replace('\n', '$') for c in block.memory]
		f.writelines(block.memory + ['\n'])

	f.close()

def init_disks():
	'''
	初始化磁盘
	'''
	from config import block

	# 初始化磁盘块
	global blocks
	blocks = [block() for _ in range(BLOCKS_MAX)]

	# 初始化磁盘块索引
	global block_indexes
	block_indexes = dict(zip([(i+1) for i in range(BLOCKS_MAX)], blocks)) # 从1开始

	# 初始化磁盘块空闲队列
	global free_blocks
	free_blocks = [i for i in range(5, BLOCKS_MAX+1)] # 1-4块为不可用块

	# 初始化根节点目录
	global root, file_num, file_dict
	root = dir('root', 1) # 从1开始
	file_num = 1

	file_indexes[1] = find_free_block_num() # 给目录属性信息也分配一个磁盘块
	file_dict[1] = root # 加入根节点索引

	block = block_indexes[file_indexes[1]]
	info_string = list('root 1')
	block.memory[:len(info_string)] = info_string # 将目录信息写入

	# 初始化当前目录结点为根节点root
	global current_root
	current_root = root

	# 初始化用户
	global user_dict
	user_dict[0] = ['admin', '1']
	user_dict[1] = ['yingjia', '1']

def init_commands():
	'''
	初始化命令
	'''
	global command_dict

	command_dict = {
		'cd' : cd, # 切换路径
		'ls' : ls, # 遍历子文件（夹）
		'clear' : clear, # 清屏
		'mkdir' : mkdir, # 创建目录
		'rmdir' : rmdir, # 删除目录
		'create' : create, # 创建文件
		'rm' : rm, # 删除文件
		'read' : read, # 读文件
		'write' : write, # 写文件
		'cp' : cp, # 复制文件
		'mv' : mv, # 移动文件
		'chmod' : chmod, # 更改文件权限(admin)
		'aduser' : aduser, # 增加用户(admin)
		'rmuser' : rmuser, # 删除用户(admin)
		'lsuser' : lsuser, # 遍历用户(admin)
		'info' : info, # 展示系统内存占用信息
		'save' : save, # 保存
		'help' : Help, # 帮助
		'logout' : logout, # 注销
		'exit' : Exit, # 退出
	}

def init_login():
	'''
	初始化登录
	'''
	print('Welcome to Yingjia File System!\n')
	
	for i in range(3): # 三次登录机会
		if login(): 
			break
		if i == 2:
			print('You have input wrong username or password 3 times.')
			print('The file system will terminate automatically.')
			exit(1)

def run():
	'''
	运行
	'''
	while True:
		prefix = '{}[{}]{}{}{}$ '.format(Fore.GREEN, current_user, Fore.BLUE, current_dir, Style.RESET_ALL)
		command = input(prefix).split()

		if not command: # 空输入异常处理
			continue

		func = command_dict.get(command[0])

		global argv
		argv = command[1:]
		if func:
			func()
		else:
			print('Command \'{}\' not found.'.format(command[0]))

def login():
	'''
	登录
	'''
	username = input('>> Please input username:\n')
	os.system('stty -echo') # 打开输入隐藏
	password = input('>> Please input password:\n')
	os.system('stty echo') # 关闭输入隐藏

	if [username, password] in user_dict.values(): # 查找成功

		global current_user, current_userid
		current_user = username # 用户名
		current_userid = int([k for k,v in user_dict.items() if v == [username, password]][0]) + 1 # 用户ID
		clear() # 清屏
		print('{}Hello, {}!{}'.format(Fore.GREEN, current_user, Style.RESET_ALL))
		return 1

	else: # 查找失败

		print('\nSorry, login failed.\n')
		return 0

def find_free_block_num():
	'''
	分配一个空闲块
	'''
	return free_blocks.pop(0) # 弹出首项

def get_time():
	'''
	获取当前时间的字符串形式
	'''
	now = datetime.datetime.now()
	now = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M:%S')
	return now

def my_input():
	'''
	允许多行输入且保留格式，以Ctrl+D结束
	'''
	lines = []
	while True:
		try:
			lines.append(input())
		except:
			break

	input_text = '\n'.join(lines) # 保留格式
	return input_text

def encoder_32(num):
	'''
	32位编码器，自动填充为4位
	'''
	return (((num == 0) and '0') or (encoder_32(num // 32).lstrip('0') + \
		'0123456789abcdefghijklmnopqrstuvwxyz'[num % 32])).zfill(4)

def decoder_32(s):
	'''
	32位解码器
	'''
	return int(s, 32)

def check_file():
	'''
	确认当前目录下是否存在文件
	'''
	for c in current_root.children:
		node = file_dict[c]
		if node.name == argv[0]:
			if isinstance(node, dir):
				return 1 # 找到目录，非文件
			else:
				return node # 找到文件
	return 0 # 未找到文件

def check_dir():
	'''
	确认当前目录下是否存在目录
	'''
	for c in current_root.children:
		node = file_dict[c]
		if node.name == argv[0]:
			if isinstance(node, file):
				return 1 # 找到文件，非目录
			else:
				return node # 找到目录
	return 0 # 未找到目录

def generate_file_id():
	'''
	生成下一个不冲突的文件ID
	'''
	start = 1
	while True:
		if start not in list(file_dict.keys()):
			return start
		else:
			start = start + 1

def cd():
	'''
	切换路径
	'''

	if len(argv) != 1:
		print('Wrong input format.\nCorrect format example: cd [parameters]')
		return

	global current_dir, current_root

	flag = -1 # 记录输入格式是绝对路径还是相对路径的标志

	try:
		# 检查路径的合法性
		if argv[0] in ['/root','~']: # 根目录
			current_dir = '/root'
			current_root = root
			return
		elif argv[0] == '..': # 返回上一层
			if current_dir != '/root':
				index = current_dir.rfind('/')
				current_dir = current_dir[:index]

				pass_nodes = current_dir.split('/')[2:]
				now_file = root
				for i in range(len(pass_nodes)): # 深度查找目标结点
					for c in now_file.children:
						if file_dict[c].name == pass_nodes[i]:
							now_file = c
							break

				current_root = now_file
				return
			else: # 避免当前就是根目录的错误判断
				return
		elif argv[0] == '/':
			return
		elif argv[0].startswith('/'): # 从根节点开始输入的绝对路径
			pass_nodes = argv[0].split('/')[2:] # 全部经过的结点
			now_file = root
			flag = 0
		else: # 相对路径
			pass_nodes = argv[0].split('/') # 全部经过的结点
			now_file = current_root
			flag = 1
	except:
		print('Wrong input format.')
		return

	try:
		for i in range(len(pass_nodes)):
			children_length = len(now_file.children) # 子节点个数
			if children_length == 0:
				raise Exception
			for j in range(children_length):
				file_node = file_dict[now_file.children[j]]
				if pass_nodes[i] == file_node.name and isinstance(file_node, dir):
					now_file = file_node
					current_root = now_file # 更新当前结点
					break
				if j == children_length-1:
					raise Exception
	except:
		print('No directory.')
		return

	# 更新当前目录和当前目录结点
	if flag:
		current_dir = current_dir + '/' + argv[0]
	else:
		current_dir = argv[0]

def ls(): 
	'''
	遍历当前目录下的文件和文件夹
	'''
	if argv:
		print('Wrong input format.\nCorrect format example: ls')
		return

	output = ' '.join([file_dict[c].name for c in current_root.children])
	
	if output: # 避免打印出空行
		print(output)

def clear():
	'''
	清空控制台
	'''
	if argv:
		print('Wrong input format.\nCorrect format example: clear')
		return
	os.system('clear')

def mkdir(): 
	'''
	创建目录
	'''
	if len(argv) != 1:
		print('Wrong input format.\nCorrect format example: mkdir test_dir')
		return

	global file_num
	file_num = file_num + 1
	id = generate_file_id()

	new_dir = dir(argv[0], id)

	if argv[0] in [file_dict[c].name for c in current_root.children]: # 当前目录下存在重名文件
		print('Please input another dir name.')
	else:
		current_root.children.append(new_dir.dir_id)
		update_dir_block(current_root) # 更新目录属性块信息

		file_indexes[id] = find_free_block_num() # 给目录属性信息也分配一个磁盘块
		file_dict[id] = new_dir # 加入文件索引

		block = block_indexes[file_indexes[id]]
		info_string = list(new_dir.name + ' ' + str(new_dir.dir_id))
		block.memory[:len(info_string)] = info_string # 将目录信息写入
	
def rmdir(): 
	'''
	删除目录总函数
	'''
	if len(argv) != 1:
		print('Wrong input format.\nCorrect format example: rmdir test_dir')
		return

	file_node = check_dir()

	if file_node == 0:
		print('Cannot rmdir a file.')
	elif not file_node:
		print('Dir not found.')
	else:
		rmdir_recursion(file_node) # 递归删除
		current_root.children.remove(file_node.dir_id) # 在当前根节点的子节点中删除该目录
		update_dir_block(current_root) # 更新目录属性块信息

def rmdir_recursion(file_node):
	'''
	递归删除目录
	'''
	global file_num

	for c in file_node.children:
		if isinstance(file_dict[c], file): # 是文件则清除文件
			clear_memory(file_dict[c])
		else: # 是目录则递归进入
			rmdir_recursion(file_dict[c])

	file_node.children = [] # 清空子节点，保证子节点引用计数为0自动清除
	file_num = file_num - 1 # 已经删除了所有的子结点，这一步减的是目录项，而目录项会被自动释放

	index = file_indexes[file_node.dir_id]
	block_indexes[index].memory = [' ' for _ in range(MEMORY_MAX)]
	free_blocks.append(index) # 加入空闲队列

	del file_indexes[file_node.dir_id] # 删除文件属性索引中的键值对
	del file_dict[file_node.dir_id] # 删除目录索引
 
def update_file_block(file_node):
	'''
	重写文件属性块
	'''
	block = block_indexes[file_indexes[file_node.file_id]]

	info_string = list(file_node.name + ' ' + \
		str(file_node.file_id) + ' ' + \
		file_node.file_time + ' ' + \
		str(file_node.create_userid) + ' ' + \
		str(file_node.index_table_len) + ' ' + \
		str(file_node.index_table) + ' ' + \
		str(file_node.last_block_len))

	block.memory = info_string + [' ' for _ in range(MEMORY_MAX - len(info_string))]

def update_dir_block(dir):
	'''
	更新目录属性块信息
	'''
	block = block_indexes[file_indexes[dir.dir_id]]

	info_string =  list(dir.name + ' ' + str(dir.dir_id) + ' ' + \
		' '.join([str(c) for c in dir.children]))

	block.memory = info_string + [' ' for _ in range(MEMORY_MAX-len(info_string))]

def create():
	'''
	创建文件
	'''
	if len(argv) != 2:
		print('Wrong input format.\nCorrect format example: create test_file w/r/_')
		return

	if argv[1] not in ['r', 'w', '_']:
		print('Only \'r\', \'w\' or \'_\' is allowed.')
		return
	else:
		access = argv[1] # 权限

	global file_num
	file_num = file_num + 1

	id = generate_file_id()

	name = argv[0] # 文件名
	file_node = file(name, id, get_time())
	file_node.create_userid = current_userid
	file_node.index_table = find_free_block_num() # 默认先分配一个块存储信息
	file_node.index_table_len = 1

	file_indexes[id] = find_free_block_num() # 再分配一个块存储属性
	file_dict[id] = file_node # 更新文件索引词典

	update_file_block(file_node) # 更新文件属性块信息
	
	access_indexes[id] = ['w', access] # 默认自己可读写，后续可通过chmod修改

	current_root.children.append(id) # 添加进当前目录的子结点

	update_dir_block(current_root) # 更新目录属性块信息

def rm():
	'''
	删除文件
	'''
	if len(argv) != 1:
		print('Wrong input format.\nCorrect format example: rm test_file')
		return

	for c in current_root.children:
		if argv[0] == file_dict[c].name:
			if isinstance(file_dict[c], file):
				clear_memory(file_dict[c])
				current_root.children.remove(c)
				update_dir_block(current_root)
			else:
				print('Please input \'rmdir\' to rm a dir.')
			return

	# 查找失败
	print('File not found.')

def read():
	'''
	读文件
	'''
	if len(argv) != 1:
		print('Wrong input format.\nCorrect format example: read test_file')
		return

	file_node = check_file()
	if file_node == 1:
		print('Cannot read a dir.')
	elif file_node == 0:
		print('File not found.')
	else:

		# 权限检查
		access_list = access_indexes[file_node.file_id]

		ok = False
		if current_userid == 1: # 为管理员
			ok = True
		elif current_userid == file_node.create_userid and access_list[0] != '_': # 为创建者
			ok = True
		elif current_userid != file_node.create_userid and access_list[1] == '_': # 为其他用户
			ok = True

		if not ok:
			print('You have no permission.')
			return

		contents = ''

		if file_node.index_table_len == 1: # 磁盘块
			block = block_indexes[file_node.index_table]
			for i in range(file_node.last_block_len):
				contents += block.memory[i]

		elif file_node.index_table_len > 1: # 一级索引
			index_block = block_indexes[file_node.index_table]

			decoder = ''.join(index_block.memory[:4 * file_node.index_table_len]) 
			decoder = re.findall('....', decoder) # 32位解码，每隔4位一切割

			apply_list = [decoder_32(i) for i in decoder]

			for i in range(file_node.index_table_len):
				block = block_indexes[apply_list[i]] # 找到文件的内存块
				if i != file_node.index_table_len - 1:
					for j in range(MEMORY_MAX): # 读文件内容
						contents += block.memory[j]
				else:
					for j in range(file_node.last_block_len):
						contents += block.memory[j]

		if contents: # 避免输出空行
			print(contents)

def write():
	'''
	写文件
	'''
	if len(argv) != 1:
		print('Wrong input format.\nCorrect format example: write test_file')
		return

	file_node = check_file()
	if file_node == 1:
		print('Cannot write to a dir.')
	elif file_node == 0:
		print('File not found.')
	else:

		# 权限检查
		access_list = access_indexes[file_node.file_id]

		ok = False
		if current_userid == 1: # 为管理员
			ok = True
		elif current_userid == file_node.create_userid and access_list[0] == 'w': # 为创建者
			ok = True
		elif current_userid != file_node.create_userid and access_list[1] == 'w': # 为其他用户
			ok = True

		if not ok:
			print('You have no permission.')
			return

		contents = my_input() # 接受输入，以Ctrl+D为结束

		# 计算并分配磁盘块
		length = len(contents)
		need_blocks = math.ceil(length / MEMORY_MAX)

		# 考虑已有磁盘块
		block = block_indexes[file_node.index_table]

		if file_node.index_table_len > 1: # 之前写入过文件，且存在索引表
			if need_blocks == 1: # 一个磁盘块

				# 释放掉索引表中的全部块
				decoder = ''.join(block.memory[:4 * file_node.index_table_len]) 
				decoder = re.findall('....', decoder) # 32位解码，每隔4位一切割

				apply_list = [decoder_32(i) for i in decoder] # 索引表中对应的磁盘号，之后依次释放

				for i in apply_list: 
					block_indexes[i].memory = [' ' for _ in range(MEMORY_MAX)]
					free_blocks.append(i) 
				
				block.memory = [' ' for _ in range(MEMORY_MAX)] # 直接索引块也要清除
				for i in range(length): # 更新内容
					block.memory[i] = contents[i]

				file_node.index_table_len = 1
				file_node.last_block_len = length # 更新文件的最后长度
				file_node.file_time = get_time()

			else: # 修改索引表
				if file_node.index_table_len == need_blocks: # 正好
					decoder = ''.join(block.memory[:4 * file_node.index_table_len]) 
					decoder = re.findall('....', decoder) # 32位解码，每隔4位一切割

					apply_list = [decoder_32(i) for i in decoder]
					for i in apply_list:
						block = block_indexes[i] # 找到一级索引表中每个索引对应的磁盘块
						if i != need_blocks - 1: # 如果不是最后一块
							for j in range(MEMORY_MAX):
								block.memory[j] = contents[j] # 把磁盘块写满
							contents = contents[MEMORY_MAX:] # 下一次从当前读到的位继续
						else: # 如果是最后一块
							last_len = (length-1) % MEMORY_MAX + 1 # 剩余未写的数目，这步是防止刚好占据满最后一块时length%MEMORY_MAX为0，却无法写入

							for j in range(last_len):
								block.memory[j] = contents[j] # 更新内容
							file_node.last_block_len = last_len # 更新文件的最后块长度

					file_node.file_time = get_time() # 更新文件的最后修改时间

				elif file_node.index_table_len > need_blocks: # 多了
					decoder = ''.join(block.memory[:4 * file_node.index_table_len]) 
					decoder = re.findall('....', decoder) # 32位解码，每隔4位一切割

					apply_list = [decoder_32(i) for i in decoder]
					delete_list = apply_list[need_blocks:] # 需要清除的块
					apply_list = apply_list[:need_blocks]

					for i in delete_list:
						block_indexes[i].memory = [' ' for _ in range(MEMORY_MAX)]
						free_blocks.append(i)

					for i in range(len(apply_list)):
						block = block_indexes[apply_list[i]] # 找到一级索引表中每个索引对应的磁盘块
						if i != need_blocks - 1: # 如果不是最后一块
							for j in range(MEMORY_MAX):
								block.memory[j] = contents[j] # 把磁盘块写满
							contents = contents[MEMORY_MAX:] # 下一次从当前读到的位继续
						else: # 如果是最后一块
							last_len = (length-1) % MEMORY_MAX + 1 # 剩余未写的数目，这步是防止刚好占据满最后一块时length%MEMORY_MAX为0，却无法写入

							for j in range(last_len):
								block.memory[j] = contents[j] # 更新内容
							file_node.last_block_len = last_len # 更新文件的最后块长度

					file_node.index_table_len = need_blocks
					file_node.file_time = get_time() # 更新文件的最后修改时间

				else: # 少了
					decoder = ''.join(block.memory[:4 * file_node.index_table_len]) 
					decoder = re.findall('....', decoder) # 32位解码，每隔4位一切割

					apply_list = [decoder_32(i) for i in decoder]
					add_list = []

					for i in range(need_blocks - file_node.index_table_len):
						add_list.append(find_free_block_num()) # 新增块

					encoder = [encoder_32(i) for i in add_list] # 32进制编码
					encoder = ''.join(encoder) # 编码后的字符串

					encoder = ''.join(decoder) + encoder # 新的索引块

					for i in range(len(encoder)): # 更新索引内容
						block.memory[i] = encoder[i]

					all_list = apply_list + add_list

					for i in range(len(all_list)):
						block = block_indexes[all_list[i]] # 找到一级索引表中每个索引对应的磁盘块
						if i != need_blocks - 1: # 如果不是最后一块
							for j in range(MEMORY_MAX):
								block.memory[j] = contents[j] # 把磁盘块写满
							contents = contents[MEMORY_MAX:] # 下一次从当前读到的位继续
						else: # 如果是最后一块
							last_len = (length-1) % MEMORY_MAX + 1 # 剩余未写的数目，这步是防止刚好占据满最后一块时length%MEMORY_MAX为0，却无法写入

							for j in range(last_len):
								block.memory[j] = contents[j] # 更新内容
							file_node.last_block_len = last_len # 更新文件的最后块长度

					file_node.index_table_len = need_blocks
					file_node.file_time = get_time() # 更新文件的最后修改时间

		else: # 未写过，或写过但只用了一个磁盘块

			if need_blocks == 1: # 一个磁盘块
				for i in range(length): # 更新内容
					block.memory[i] = contents[i]
				file_node.last_block_len = length # 更新文件的最后长度
				file_node.file_time = get_time()

			elif need_blocks > 128: # 一级索引无法满足
				print('Sorry, the file is so large.')
				return

			else: # 一级索引
				file_node.index_table_len = need_blocks # 更新索引表长度

				apply_list = [] # 申请块的号码
				for _ in range(need_blocks):
					apply_list.append(find_free_block_num())

				encoder = [encoder_32(i) for i in apply_list] # 32进制编码
				encoder = ''.join(encoder) # 编码后的字符串

				for i in range(len(encoder)): # 更新索引内容
					block.memory[i] = encoder[i]

				for i in range(need_blocks):
					block = block_indexes[apply_list[i]] # 找到一级索引表中每个索引对应的磁盘块
					if i != need_blocks - 1: # 如果不是最后一块
						for j in range(MEMORY_MAX):
							block.memory[j] = contents[j] # 把磁盘块写满
						contents = contents[MEMORY_MAX:] # 下一次从当前读到的位继续
					else: # 如果是最后一块
						last_len = (length-1) % MEMORY_MAX + 1 # 剩余未写的数目，这步是防止刚好占据满最后一块时length%MEMORY_MAX为0，却无法写入

						for j in range(last_len):
							block.memory[j] = contents[j] # 更新内容
						file_node.last_block_len = last_len # 更新文件的最后块长度

				file_node.file_time = get_time() # 更新文件的最后修改时间

		# 重写文件属性块
		update_file_block(file_node) 

def cp():
	'''
	复制文件
	'''
	if len(argv) != 2:
		print('Wrong input format.\nCorrect format example: cp test_file /root/test')
		return

	# 首先检查文件是否在目录下
	file_node = check_file()

	if file_node == 1:
		print('Cannot cp a dir.')
		return
	elif file_node == 0:
		print('File not found.')
		return

	# 创建一个新的类实例
	global file_num 

	id = generate_file_id()

	new_file_node = file(argv[0], id, get_time())
	new_file_node.create_userid = current_userid
	new_file_node.index_table = find_free_block_num() # 默认先分配一个块存储信息
	new_file_node.index_table_len = 1

	file_indexes[id] = find_free_block_num() # 再分配一个块存储属性
	file_dict[id] = new_file_node

	update_file_block(new_file_node)
	
	access_indexes[id] = access_indexes[file_node.file_id] # 默认自己可读写，后续可通过chmod修改

	# 再检查拷贝目录的合法性，并复制
	pass_nodes = argv[1].split('/')[2:]

	try:
		now_file = root
		for i in range(len(pass_nodes)):
			children_length = len(now_file.children) # 子节点个数
			if children_length == 0:
				raise Exception
			for j in range(children_length):
				file_node = file_dict[now_file.children[j]]
				if pass_nodes[i] == file_node.name and isinstance(file_node, dir):
					now_file = file_node
					now_file.children.append(new_file_node.file_id) # 新对象添加进对应位置
					update_dir_block(now_file)
					file_num = file_num + 1 # 文件计数加1
					break
				if j == children_length-1:
					raise Exception

		if not pass_nodes: # 说明拷贝到根目录下，特判
			now_file.children.append(new_file_node.file_id) # 新对象添加进对应位置
			update_dir_block(now_file)
			file_num = file_num + 1 # 文件计数加1
	except:
		print('No directory.')
		return

def mv():
	'''
	移动文件
	'''
	cp() # 先复制文件

	file_node = check_file()
	if file_node == 1:
		print('Cannot mv a dir.')
		return
	elif file_node == 0:
		print('File not found.')
		return

	clear_memory(file_node) # 清除文件属性和文件信息占用的内存、文件属性块索引词典中的键值对
	current_root.children.remove(file_node.file_id) # 再把原文件删除即可
	update_dir_block(current_root) # 更新目录块

def clear_memory(file_node):
	'''
	清除文件属性和文件信息占用的内存、文件属性块索引词典中的键值对
	'''

	# 文件信息块
	if file_node.index_table_len == 1: # 磁盘块
		index = file_node.index_table
		block_indexes[index].memory = [' ' for _ in range(MEMORY_MAX)]
		free_blocks.append(index)

	elif file_node.index_table_len > 1: # 索引表
		block = block_indexes[file_node.index_table]

		contents = ''.join(block.memory[:4 * file_node.index_table_len]) 
		decoder = re.findall('....', contents) # 32位解码，每隔4位一切割

		apply_list = [decoder_32(i) for i in decoder] # 索引表中对应的磁盘号，之后依次释放

		for i in apply_list: 
			block_indexes[i].memory = [' ' for _ in range(MEMORY_MAX)]
			free_blocks.append(i) 
		
		block.memory = [' ' for _ in range(MEMORY_MAX)] # 直接索引块也要释放
		free_blocks.append(file_node.index_table)

	# 文件属性块
	index = file_indexes[file_node.file_id]
	block_indexes[index].memory = [' ' for _ in range(MEMORY_MAX)]
	free_blocks.append(index)

	del file_indexes[file_node.file_id] # 删除文件属性索引
	del file_dict[file_node.file_id]
	del access_indexes[file_node.file_id] # 删除权限索引

	global file_num
	file_num = file_num - 1 # 文件数减一

def chmod():
	'''
	更改文件权限
	'''
	if len(argv) != 3:
		print('Wrong input format.\nCorrect format example: chmod test_file r s')
		return

	if argv[1] not in ['r', 'w']:
		print('Only \'r\' and \'w\' is allowed.')
		return

	if argv[2] not in ['s', 'o']: # self others
		print('Only \'self\' or \'others\' is allowed.')
		return

	# 首先检查文件是否在当前目录下
	file_node = check_file()
	if file_node == 1:
		print('Cannot chmod a dir.')
	elif file_node == 0:
		print('File not found.')
	else:
		if current_userid == 1 or file_node.create_userid == current_userid: # admin和创建者可以修改
			if argv[2] == 's':
				access_indexes[file_node.file_id][0] = argv[1]
			else:
				access_indexes[file_node.file_id][1] = argv[2]
			print('Chmod successfully.')
		else:
			print('You have no permission.')

def aduser(): 
	'''
	增加用户
	'''
	if len(argv) != 2:
		print('Wrong input format.\nCorrect format example: aduser yingjia 123')
		return
	elif argv[0] in user_dict.keys(): # 与已有用户重名
		print('Please input another username.')
		return
	if current_userid == 1:
		next_id = len(user_dict.keys())
		user_dict[next_id] = [argv[0], argv[1]] # 账号 密码
	else:
		print('You have no permission.')

def rmuser(): 
	'''
	删除用户
	'''
	if len(argv) != 1: 
		print('Wrong input format.\nCorrect format example: rmuser yingjia')
		return
	if current_userid == 1:
		if argv[0] == 'admin':
			print('Admin is not allowed to rm.')
			return
		for item in list(user_dict.items()):
			if argv[0] == item[1][0]:
				del user_dict[item[0]]
				break
	else:
		print('You have no permission.')

def lsuser(): 
	'''
	展示当前所有用户和密码
	'''
	if argv: 
		print('Wrong input format.\nCorrect input format: lsuser')
		return

	if current_userid == 1:
		print('UserID    Username    Password')
		for item in list(user_dict.items()): # 不用担心user_dict为空的情况
			print('{:<10s}{:<12s}{:<8s}'.format(str(item[0]), item[1][0], item[1][1]))
	else:
		print('You have no permission.')

def info(): 
	'''
	显示系统信息
	'''

	# 用户个数
	print('User = ' + str(len(user_dict)))

	# 文件个数(包括目录)
	print('File/Dir = ' + str(len(file_indexes)))

	# 磁盘块个数
	print('Blocks = ' + str(BLOCKS_MAX))

	# 空闲磁盘块个数
	print('Free Blocks = ' + str(len(free_blocks)))

	# 磁盘块占用率
	blocks_occ_rate = (1 - len(free_blocks) / BLOCKS_MAX) * 100
	print('Blocks Occupancy Rate = {:.2f}%'.format(blocks_occ_rate))

def logout(): 
	'''
	注销
	'''
	init_login() # 初始化登录

def Exit(): 
	'''
	退出
	'''
	print('Bye.')
	save() # 自动保存
	exit(0)

if __name__ == '__main__':

	config = config()
	MEMORY_MAX = config.MEMORY_MAX # 每一个磁盘块的最大容量
	BLOCKS_MAX = config.BLOCKS_MAX # 磁盘块的最大个数

	current_user = '' # 当前用户，空字符串表示未登录
	current_userid = 0 # 当前用户ID，0表示未登录

	current_dir = '/root' # 当前目录
	root = None # 根节点
	current_root = None # 当前目录结点

	argv = [] # 命令行参数

	command_dict = {} # 命令与函数映射字典

	user_dict = {} # 用户字典

	free_blocks = [] # 磁盘块号空闲队列
	blocks = [] # 磁盘块列表
	block_indexes = {} # 磁盘块索引词典, key为磁盘块号，value为磁盘块

	file_num = 0 # 文件个数（包括目录），用来分配ID
	file_indexes = {} # 文件和保存文件属性的块的索引词典，key为文件ID，value为块号
	file_dict = {} # 文件与文件结点的映射词典，key为文件ID，value为类实例

	access_indexes = {} # 权限索引词典，第一层key为文件ID，value为分别表示对自己和对其他用户的权限
	
	try:
		f = open('filesystem', 'r')
		load(f) # 读取文件系统数据
		print('Load successfully!')
		f.close()
	except:
		init_disks() # 初始化磁盘
		print('Init successfully!')

	init_commands() # 初始化命令
	init_login() # 初始化登录
	run() # 运行


