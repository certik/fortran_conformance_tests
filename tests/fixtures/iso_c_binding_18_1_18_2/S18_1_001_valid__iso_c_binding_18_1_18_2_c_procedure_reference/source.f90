! rule: S18.1-001
! covers: reference-c-defined-procedure reference-c-prototype-described-procedure
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_procedure_reference
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  interface
    integer(c_int) function c_add_one(value) bind(c, name="batch310_add_one")
      import c_int
      integer(c_int), value :: value
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(c_add_one(41_c_int), 42_c_int, 'C defined function result')
  call expect_int(proto_times_three(12_c_int), 36_c_int, 'C prototype described Fortran function')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.1 C PROCEDURE REFERENCE OK'
contains
  integer(c_int) function proto_times_three(value) bind(c)
    integer(c_int), value :: value
    proto_times_three = value * 3_c_int
  end function
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
