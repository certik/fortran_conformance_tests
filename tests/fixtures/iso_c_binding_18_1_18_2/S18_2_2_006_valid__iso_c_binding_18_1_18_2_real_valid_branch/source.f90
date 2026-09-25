! rule: S18.2.2-006
! covers: real-kind-valid-branch
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_real_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_long_double
  implicit none
  interface
    real(c_float) function c_float_add_one(value) bind(c, name="batch310_float_add_one")
      import c_float
      real(c_float), value :: value
    end function
    real(c_double) function c_double_add_one(value) bind(c, name="batch310_double_add_one")
      import c_double
      real(c_double), value :: value
    end function
    real(c_long_double) function c_long_double_add_one(value) bind(c, name="batch310_long_double_add_one")
      import c_long_double
      real(c_long_double), value :: value
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(0.0_c_float), c_float, 'C_FLOAT direct kind inquiry')
  call expect_int(kind(0.0_c_double), c_double, 'C_DOUBLE direct kind inquiry')
  call expect_int(kind(0.0_c_long_double), c_long_double, 'C_LONG_DOUBLE direct kind inquiry')
  call expect_logical(c_float_add_one(1.5_c_float) == 2.5_c_float, .true., 'C_FLOAT exact C roundtrip')
  call expect_logical(c_double_add_one(1.5_c_double) == 2.5_c_double, .true., 'C_DOUBLE exact C roundtrip')
  call expect_logical(c_long_double_add_one(1.5_c_long_double) == 2.5_c_long_double, .true., 'C_LONG_DOUBLE exact C roundtrip')
  call expect_int(checks, 6_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 REAL VALID BRANCH OK'

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
