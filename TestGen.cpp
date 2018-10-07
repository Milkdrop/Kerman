#include <iostream>
#include <stdio.h>
#include <random>
#include <time.h>
using namespace std;

int RandomRange(int x, int y) {
    return rand() % (y - x + 1) + x;
}

int main(int argc, char *argv[]) {
    srand(time(0) + atoi(argv[1]));
	
	int x = RandomRange(1, 1000000);
	printf ("%d", x);
	/*
    int m = RandomRange(3, 1000);
    int n = RandomRange(3, 1000);
	printf("%d %d\n", m, n);
	
    for (int i = 0; i < m; i++) {
        for (int k = 0; k < n; k++) {
            int choice = RandomRange(0, 1);
            if (choice == 0)
                printf(".");
            else
                printf("#");
        }
        printf ("\n");
    }*/
}
