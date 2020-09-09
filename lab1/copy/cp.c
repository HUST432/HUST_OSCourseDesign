#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#define bufsize 4

int main(int argc, const char* argv[])
{
	int f_read = open(argv[1], O_RDONLY);
	if(f_read == -1)
	{
		printf("打开%s失败！\n", argv[1]);
		return -1;
	}

	int f_write = open(argv[2], O_RDWR|O_CREAT|O_TRUNC); //O_TRUNC -> 存在且可写时会清除原来信息
	if(f_write == -1)
	{
		printf("打开或创建%s失败！\n", argv[2]);
		return -1;
	}

	char buf[bufsize]; //缓冲区
	int num = 0;

	while((num = read(f_read, buf, bufsize)) > 0)
	{
		write(f_write, buf, num);
	}
	printf("拷贝成功！\n");

	close(f_read);
	close(f_write);

	return 0;
}