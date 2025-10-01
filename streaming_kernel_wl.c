
#include <stdio.h>
#include <stdlib.h>

// Define the size of the arrays.
// 8M elements * 8 bytes/double * 3 arrays = 192 MB of data.
// This is significantly larger than a typical L2 cache (e.g., 256KB - 4MB).
#define ARRAY_SIZE (512 * 1024 )

// The number of times to repeat the main kernel loop.
#define NUM_REPETITIONS 10

int main() {
    // Allocate three large arrays on the heap.
    double* a = (double*)malloc(ARRAY_SIZE * sizeof(double));
    double* b = (double*)malloc(ARRAY_SIZE * sizeof(double));
    double* c = (double*)malloc(ARRAY_SIZE * sizeof(double));

    if (a == NULL || b == NULL || c == NULL) {
        perror("Failed to allocate memory for arrays");
        // Free any that might have been successfully allocated
        free(a);
        free(b);
        free(c);
        return 1;
    }

    // Initialize the source arrays with some values.
    for (size_t i = 0; i < ARRAY_SIZE; ++i) {
        b[i] = 2.0;
        c[i] = 3.0;
    }

    const double scalar = 1.5;

    printf("Starting streaming memory access kernel...\n");

    // --- The Streaming Kernel ---
    // Repeat the kernel to ensure the simulation runs long enough
    // to gather meaningful statistics.
    for (int rep = 0; rep < NUM_REPETITIONS; ++rep) {
        for (size_t i = 0; i < ARRAY_SIZE; ++i) {
            // This is the STREAM Triad operation.
            a[i] = b[i] + scalar * c[i];
        }
    }

    // Use a volatile variable to read from the array to ensure the compiler
    // does not optimize away the main loop.
    volatile double result = a[ARRAY_SIZE / 2];

    printf("Streaming kernel complete. Result (to prevent optimization): %f\n", result);

    // Clean up allocated memory.
    free(a);
    free(b);
    free(c);

    return 0;
}
