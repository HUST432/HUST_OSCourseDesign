asmlinkage long sys_mycopy(const char* file1, const char* file2)
{
	char buf[128]; // 缓冲区

	mm_segment_t old_fs = get_fs(); // 保存原来的段
	set_fs(KERNEL_DS); // 设置为数据段

	int f_read, f_write;

	f_read = sys_open(file1,O_RDONLY,0);
	if(f_read == -1)
		return -1;

	f_write = sys_open(file2, O_WRONLY|O_CREAT|O_TRUNC, S_IRUSR|S_IWUSR); //提供给用户读写权限
	if(f_write == -1)
		return -1;

	int num;
	while((num = sys_read(f_read, buf, 128)) > 0)
	{
		sys_write(f_write, buf, num);
	}

	set_fs(old_fs); // 还原
	return 0;
}