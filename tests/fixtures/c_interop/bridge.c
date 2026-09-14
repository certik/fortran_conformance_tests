int calibration_scale(int n, int *values)
{
    int total = 0;
    for (int i = 0; i < n; ++i) {
        values[i] *= 2;
        total += values[i];
    }
    return total;
}
