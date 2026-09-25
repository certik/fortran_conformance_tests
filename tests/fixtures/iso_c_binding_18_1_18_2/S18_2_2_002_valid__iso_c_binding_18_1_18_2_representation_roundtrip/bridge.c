#include <stdbool.h>
int batch310_int_roundtrip(int value) { return value; }
float batch310_float_add_one(float value) { return value + 1.0f; }
double batch310_double_add_one(double value) { return value + 1.0; }
long double batch310_long_double_add_one(long double value) { return value + 1.0L; }
int batch310_bool_codes(_Bool t, _Bool f) { return (t == (_Bool)1 && f == (_Bool)0) ? 10 : -10; }
int batch310_char_code(char ch) { return ch == 'A' ? 65 : -65; }
