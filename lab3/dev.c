#include "linux/kernel.h"
#include "linux/module.h"
#include "linux/fs.h"
#include "linux/init.h"
#include "linux/types.h"
#include "linux/errno.h"
#include "linux/uaccess.h"
#include "linux/kdev_t.h"
 
// 函数声明
int my_open(struct inode *inode, struct file *file);
int my_release(struct inode *inode, struct file *file);
ssize_t my_read(struct file *file, char __user *user, size_t t, loff_t *f);
ssize_t my_write(struct file *file, const char __user *user, size_t t, loff_t *f);
 

int id;//设备号

char message[32] = "Welcome to new devdriver!";
 
struct file_operations fops = {
	.open = my_open, 
	.release = my_release, 
	.read = my_read, 
	.write = my_write
};

MODULE_LICENSE("GPL"); //模块许可证
 
int init_module()
//注册模块
{
	int ans = register_chrdev(0, "test", &fops);
	if(ans < 0)
	{
		printk("Register unsuccessfully.\n");
		return -1;
	}
	else
	{
		printk("Register successfully.\n");
		printk("id: %d\n", ans);

		id = ans;
		return 0;
	}
}

void cleanup_module()
//退出模块
{
	unregister_chrdev(id, "test");
	printk("Unregister successfully.\n");
}


int my_open(struct inode *inode, struct file *file)
{
	try_module_get(THIS_MODULE);

	return 0;
}

int my_release(struct inode *inode, struct file *file)
{
	module_put(THIS_MODULE);
 
	return 0;
}

ssize_t my_read(struct file *file, char __user *user, size_t t, loff_t *f)
{
	int ans = copy_to_user(user,message,sizeof(message)); //成功返回0，失败返回没有拷贝的字节数
	if(ans)
		return -1;
	return sizeof(message);
}

ssize_t my_write(struct file *file, const char __user *user, size_t t, loff_t *f)
{
	int ans = copy_from_user(message,user,sizeof(message)); //成功返回0，失败返回没有拷贝的字节数
	if(ans)
		return -1;
	return sizeof(message);
}
