#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>

int main()
{
	char buf[32];
 
	int dev = open("/dev/test", O_RDWR);
 
	if(dev == -1)
	{
		printf("Open failed.\n");
		exit(1);
	}
	//读初始信息
	read(dev, buf, sizeof(buf));
	printf("%s\n", buf);

	//写信息
	printf("Input new message: ");
	gets(buf);
	write(dev, buf, sizeof(buf));
 
	//读信息
	read(dev, buf, sizeof(buf)); 
	printf("Output new message: %s\n", buf);
		
	close(dev);

	return 0;
}

