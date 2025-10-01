
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// The total number of nodes in our memory pool.
// This should be large enough to exceed the L2 cache size to stress main memory.
#define NUM_NODES (1024 * 512) // 1M nodes

// The number of pointer-chasing operations to perform.
#define NUM_TRAVERSALS (NUM_NODES * 4)

// Define the structure of each node in the linked list.
struct Node {
    // Some payload data to ensure the node is the size of a cache line
    // and to prevent the compiler from optimizing away the memory access.
    long long data[6];
    struct Node* next; // The pointer to the next node.
};

int main() {
    // Allocate a contiguous block of memory for all nodes.
    struct Node* nodes = (struct Node*)malloc(NUM_NODES * sizeof(struct Node));
    if (nodes == NULL) {
        perror("Failed to allocate memory for nodes");
        return 1;
    }

    // Create an array of indices to shuffle, from 0 to NUM_NODES - 1.
    int* indices = (int*)malloc(NUM_NODES * sizeof(int));
    if (indices == NULL) {
        perror("Failed to allocate memory for indices");
        free(nodes);
        return 1;
    }

    for (int i = 0; i < NUM_NODES; ++i) {
        indices[i] = i;
        nodes[i].data[0] = i; // Initialize some data
    }

    // --- Create the pseudo-random traversal path ---
    // Seed the random number generator.
    srand(time(NULL));

    // Shuffle the indices array using the Fisher-Yates algorithm.
    // This creates a random permutation of the node indices.
    for (int i = NUM_NODES - 1; i > 0; --i) {
        int j = rand() % (i + 1);
        int temp = indices[i];
        indices[i] = indices[j];
        indices[j] = temp;
    }

    // Link the nodes together according to the shuffled indices.
    // This creates the pointer-chasing chain.
    for (int i = 0; i < NUM_NODES - 1; ++i) {
        nodes[indices[i]].next = &nodes[indices[i + 1]];
    }
    // Make the list circular by linking the last node back to the first.
    nodes[indices[NUM_NODES - 1]].next = &nodes[indices[0]];


    // --- The Pointer-Chasing Kernel ---
    printf("Starting pointer chasing traversal...\n");

    struct Node* p = &nodes[indices[0]]; // Start at the beginning of the shuffled list
    
    // Use a volatile variable to ensure the compiler does not optimize away the loop.
    volatile long long sum = 0;

    for (long long i = 0; i < NUM_TRAVERSALS; ++i) {
        // The core dependency: the next value of 'p' depends on the current load.
        // We also read some data from the node to make the load meaningful.
        sum += p->data[0];
        p = p->next;
    }

    printf("Traversal complete. Final sum (to prevent optimization): %lld\n", sum);

    // Clean up allocated memory.
    free(indices);
    free(nodes);

    return 0;
}
