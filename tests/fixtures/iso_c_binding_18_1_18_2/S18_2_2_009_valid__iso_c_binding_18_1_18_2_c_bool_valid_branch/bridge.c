#include <stdbool.h>
int batch310_bool_codes(_Bool t, _Bool f) { return (t == (_Bool)1 && f == (_Bool)0) ? 10 : -10; }
