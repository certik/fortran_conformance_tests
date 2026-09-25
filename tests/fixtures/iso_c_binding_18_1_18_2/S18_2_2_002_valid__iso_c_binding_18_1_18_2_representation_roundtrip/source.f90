! rule: S18.2.2-002
! covers: c-compatible-kind-representation c-bool-true-false-representation
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_representation_roundtrip
  use, intrinsic :: iso_c_binding, only: c_int, c_float, c_double, c_long_double, c_bool, c_char
  implicit none
  interface
    integer(c_int) function c_int_roundtrip(value) bind(c, name="batch310_int_roundtrip")
      import c_int
      integer(c_int), value :: value
    end function
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
    integer(c_int) function c_bool_codes(t, f) bind(c, name="batch310_bool_codes")
      import c_int, c_bool
      logical(c_bool), value :: t, f
    end function
    integer(c_int) function c_char_code(ch) bind(c, name="batch310_char_code")
      import c_int, c_char
      character(kind=c_char), value :: ch
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(c_int_roundtrip(-3_c_int), -3_c_int, 'integer(C_INT) C representation negative')
  call expect_int(c_int_roundtrip(42_c_int), 42_c_int, 'integer(C_INT) C representation positive')
  call expect_logical(c_float_add_one(1.5_c_float) == 2.5_c_float, .true., 'C_FLOAT exact roundtrip')
  call expect_logical(c_double_add_one(1.5_c_double) == 2.5_c_double, .true., 'C_DOUBLE exact roundtrip')
  call expect_logical(c_long_double_add_one(1.5_c_long_double) == 2.5_c_long_double, .true., 'C_LONG_DOUBLE exact roundtrip')
  call expect_int(c_bool_codes(.true._c_bool, .false._c_bool), 10_c_int, 'C_BOOL true false C codes')
  call expect_int(c_char_code(c_char_'A'), 65_c_int, 'C_CHAR C char value')
  call expect_int(checks, 7_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 REPRESENTATION ROUNDTRIP OK'

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
