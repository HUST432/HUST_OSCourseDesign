class config():
	'''
	配置参数
	'''
	def __init__(self):
		self.MEMORY_MAX = 512 # 每一个磁盘块的最大容量
		self.BLOCKS_MAX = 20 # 磁盘块的最大个数

class block():
	'''
	磁盘块
	'''
	def __init__(self):
		self.memory = [' ' for _ in range(config().MEMORY_MAX)] # 内存

class file():
	'''
	信息文件
	'''
	def __init__(self, name, file_id, file_time):
		self.name = name # 文件名
		self.file_id = file_id # 文件ID
		self.file_time = file_time # 最后修改时间
		self.create_userid = None # 创建者ID
		self.index_table_len = 0 # 文件索引表长度，大于1表示用到了一级索引
		self.index_table = None # 文件索引表（也可能为单个磁盘块）ID
		self.last_block_len = 0 # 占用最后一个块的长度

class dir():
	'''
	目录文件
	'''
	def __init__(self, name, dir_id):
		self.name = name # 目录名
		self.dir_id = dir_id # 目录ID
		self.children = [] # 子节点,保存的是子节点的id


