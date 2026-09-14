#include <ISO_Fortran_binding.h>
#include <stddef.h>
#include <stdio.h>

int check_descriptor(const CFI_cdesc_t *x, int tag, const int *aliases)
{
    const CFI_type_t integer_codes[] = {
        CFI_type_signed_char, CFI_type_short, CFI_type_int, CFI_type_long,
        CFI_type_long_long, CFI_type_size_t, CFI_type_int8_t, CFI_type_int16_t,
        CFI_type_int32_t, CFI_type_int64_t, CFI_type_int_least8_t,
        CFI_type_int_least16_t, CFI_type_int_least32_t, CFI_type_int_least64_t,
        CFI_type_int_fast8_t, CFI_type_int_fast16_t, CFI_type_int_fast32_t,
        CFI_type_int_fast64_t, CFI_type_intmax_t, CFI_type_intptr_t,
        CFI_type_ptrdiff_t
    };
    const CFI_type_t real_codes[] = {
        CFI_type_float, CFI_type_double, CFI_type_long_double
    };
    const size_t real_lengths[] = {
        sizeof(float), sizeof(double), sizeof(long double)
    };
    size_t expected_length = 0;
    int type_matches = 0;

    if (x == NULL || aliases == NULL) return 1;
    if (x->version != CFI_VERSION) {
        fprintf(stderr, "tag %d: descriptor version %d, expected %d\n",
                tag, x->version, (int)CFI_VERSION);
        return 2;
    }
    if (x->base_addr == NULL) return 3;
    if (x->rank != 0) return 4;
    switch (tag) {
    case 1:
        expected_length = sizeof(int);
        for (size_t i = 0; i < sizeof(integer_codes) / sizeof(integer_codes[0]); ++i) {
            if (aliases[i] == 1 && integer_codes[i] > 0 && x->type == integer_codes[i])
                type_matches = 1;
        }
        break;
    case 2:
    case 3:
        for (size_t i = 0; i < sizeof(real_codes) / sizeof(real_codes[0]); ++i) {
            if (aliases[i] == 1 && real_codes[i] > 0 && x->type == real_codes[i]) {
                type_matches = 1;
                expected_length = real_lengths[i];
            }
        }
        break;
    case 4:
        expected_length = 3;
        type_matches = aliases[0] == 1 && CFI_type_char > 0 && x->type == CFI_type_char;
        break;
    case 5:
        expected_length = 5;
        type_matches = aliases[0] == 1 && CFI_type_char > 0 && x->type == CFI_type_char;
        break;
    default:
        return 5;
    }
    if (!type_matches || x->elem_len != expected_length) {
        fprintf(stderr, "tag %d: type %d, kind-matched code %d, elem_len %zu/%zu\n",
                tag, (int)x->type, type_matches,
                (size_t)x->elem_len, expected_length);
        return 7;
    }
    return 0;
}
