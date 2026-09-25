! rule: S18.2.2-007
! covers: float-complex-kind-equals-float double-complex-kind-equals-double long-double-complex-kind-equals-long-double
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_complex_kind_equalities
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_long_double, c_float_complex, c_double_complex, c_long_double_complex
  implicit none
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_logical(c_float_complex == c_float, .true., 'C_FLOAT_COMPLEX equals C_FLOAT')
  call expect_logical(c_double_complex == c_double, .true., 'C_DOUBLE_COMPLEX equals C_DOUBLE')
  call expect_logical(c_long_double_complex == c_long_double, .true., 'C_LONG_DOUBLE_COMPLEX equals C_LONG_DOUBLE')
  call expect_int(checks, 3_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 COMPLEX KIND EQUALITIES OK'

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
