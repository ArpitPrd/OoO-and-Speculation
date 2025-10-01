
#include <stdio.h>
#include <stdlib.h>

// Define the number of iterations for the main computation loop.
// A large number is chosen to make the program run long enough for analysis.
#define NUM_ITERATIONS 100000

// This function performs a chain of dependent floating-point operations.
// The dependency (result is used in the next calculation) tests the CPU's
// ability to forward results efficiently through its execution units.
double perform_computation(double val) {
    double result = val;
    // This inner loop increases the computation-to-memory ratio.
    for (int i = 0; i < 50; ++i) {
        result = result * 1.0001 + 0.1;
        result = result * 0.9999 - 0.1;
    }
    return result;
}

int main() {
    double value = 1.234567;

    printf("Starting compute-bound workload...\n");

    // --- The Compute-Bound Kernel ---
    // The main loop repeatedly calls the computation function.
    for (long i = 0; i < NUM_ITERATIONS; ++i) {
        value = perform_computation(value);
    }

    // Use a volatile variable to store the final result.
    // This is a standard technique to prevent an optimizing compiler from
    // recognizing that the loop's result is unused and removing it entirely.
    volatile double final_result = value;

    printf("Compute-bound workload complete. Final result (to prevent optimization): %f\n", final_result);

    return 0;
}
