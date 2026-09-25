! rule: S18.2.2-001
! covers: table-18-2-default-integer-named-constants
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_default_integer_constants
  use, intrinsic :: iso_c_binding, only: c_int, c_signed_char, c_short, c_int, c_long, c_long_long, c_size_t, c_int8_t, c_int16_t, c_int32_t, c_int64_t, c_int_least8_t, c_int_least16_t, c_int_least32_t, c_int_least64_t, c_int_fast8_t, c_int_fast16_t, c_int_fast32_t, c_int_fast64_t, c_intmax_t, c_intptr_t, c_ptrdiff_t, c_float, c_double, c_long_double, c_float_complex, c_double_complex, c_long_double_complex, c_bool, c_char
  implicit none
  integer, parameter :: default_kind = kind(0)
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(c_signed_char), default_kind, 'c_signed_char default integer kind')
  call expect_int(kind(c_short), default_kind, 'c_short default integer kind')
  call expect_int(kind(c_int), default_kind, 'c_int default integer kind')
  call expect_int(kind(c_long), default_kind, 'c_long default integer kind')
  call expect_int(kind(c_long_long), default_kind, 'c_long_long default integer kind')
  call expect_int(kind(c_size_t), default_kind, 'c_size_t default integer kind')
  call expect_int(kind(c_int8_t), default_kind, 'c_int8_t default integer kind')
  call expect_int(kind(c_int16_t), default_kind, 'c_int16_t default integer kind')
  call expect_int(kind(c_int32_t), default_kind, 'c_int32_t default integer kind')
  call expect_int(kind(c_int64_t), default_kind, 'c_int64_t default integer kind')
  call expect_int(kind(c_int_least8_t), default_kind, 'c_int_least8_t default integer kind')
  call expect_int(kind(c_int_least16_t), default_kind, 'c_int_least16_t default integer kind')
  call expect_int(kind(c_int_least32_t), default_kind, 'c_int_least32_t default integer kind')
  call expect_int(kind(c_int_least64_t), default_kind, 'c_int_least64_t default integer kind')
  call expect_int(kind(c_int_fast8_t), default_kind, 'c_int_fast8_t default integer kind')
  call expect_int(kind(c_int_fast16_t), default_kind, 'c_int_fast16_t default integer kind')
  call expect_int(kind(c_int_fast32_t), default_kind, 'c_int_fast32_t default integer kind')
  call expect_int(kind(c_int_fast64_t), default_kind, 'c_int_fast64_t default integer kind')
  call expect_int(kind(c_intmax_t), default_kind, 'c_intmax_t default integer kind')
  call expect_int(kind(c_intptr_t), default_kind, 'c_intptr_t default integer kind')
  call expect_int(kind(c_ptrdiff_t), default_kind, 'c_ptrdiff_t default integer kind')
  call expect_int(kind(c_float), default_kind, 'c_float default integer kind')
  call expect_int(kind(c_double), default_kind, 'c_double default integer kind')
  call expect_int(kind(c_long_double), default_kind, 'c_long_double default integer kind')
  call expect_int(kind(c_float_complex), default_kind, 'c_float_complex default integer kind')
  call expect_int(kind(c_double_complex), default_kind, 'c_double_complex default integer kind')
  call expect_int(kind(c_long_double_complex), default_kind, 'c_long_double_complex default integer kind')
  call expect_int(kind(c_bool), default_kind, 'c_bool default integer kind')
  call expect_int(kind(c_char), default_kind, 'c_char default integer kind')
  call expect_int(checks, 29_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 DEFAULT INTEGER CONSTANTS OK'

contains
  subroutine expect_int(actual, expected, label)
    integer(c_int), intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_logical(actual, expected, label)
    logical, intent(in) :: actual, expected
    character(len=*), intent(in) :: label
    if (actual .neqv. expected) then
      write(*,'(a,1x,a,1x,l1,1x,l1)') 'ISO-C-BINDING-CHECK-FAIL', label, actual, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program
