#include <sys/syscall.h>
#include <unistd.h>

int main()
{
	syscall(333, "file1.txt", "file2.txt");
	return 0;
}