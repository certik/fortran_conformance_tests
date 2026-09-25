! rule: S18.2.2-004
! covers: optional-integer-kind-valid-branch
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_optional_integer_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_short, c_long, c_long_long, c_size_t, c_int8_t, c_int16_t, c_int32_t, c_int64_t
  implicit none
  integer(c_short) :: s
  integer(c_long) :: l
  integer(c_long_long) :: ll
  integer(c_size_t) :: n
  integer(c_int8_t) :: i8
  integer(c_int16_t) :: i16
  integer(c_int32_t) :: i32
  integer(c_int64_t) :: i64
  integer(c_int) :: checks
  checks = 0_c_int
  s = 5_c_short; l = 6_c_long; ll = 7_c_long_long; n = 8_c_size_t
  i8 = 2_c_int8_t; i16 = 3_c_int16_t; i32 = 4_c_int32_t; i64 = 5_c_int64_t
  call expect_int(kind(s), c_short, 'C_SHORT valid integer kind')
  call expect_int(kind(l), c_long, 'C_LONG valid integer kind')
  call expect_int(kind(ll), c_long_long, 'C_LONG_LONG valid integer kind')
  call expect_int(kind(n), c_size_t, 'C_SIZE_T valid integer kind')
  call expect_int(kind(i8), c_int8_t, 'C_INT8_T valid integer kind')
  call expect_int(kind(i16), c_int16_t, 'C_INT16_T valid integer kind')
  call expect_int(kind(i32), c_int32_t, 'C_INT32_T valid integer kind')
  call expect_int(kind(i64), c_int64_t, 'C_INT64_T valid integer kind')
  call expect_int(checks, 8_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 OPTIONAL INTEGER VALID BRANCH OK'

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
