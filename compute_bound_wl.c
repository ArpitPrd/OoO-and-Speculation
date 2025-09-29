int main() {
    int N = 1e5;
    int x = 198279847;
    int y = 783817687;
    int z = 378928344;

    for (int i = 0; i < N; i++) {
        z = z + x * y;
        y = y ^ x;
        x = x & z;
    }
}