! rule: S18.2.2-009
! covers: c-bool-valid-logical-kind-branch
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_bool_valid_branch
  use, intrinsic :: iso_c_binding, only: c_int, c_bool
  implicit none
  interface
    integer(c_int) function c_bool_codes(t, f) bind(c, name="batch310_bool_codes")
      import c_int, c_bool
      logical(c_bool), value :: t, f
    end function
  end interface
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_int(kind(.true._c_bool), c_bool, 'C_BOOL direct kind inquiry')
  call expect_int(c_bool_codes(.true._c_bool, .false._c_bool), 10_c_int, 'C_BOOL C _Bool true false')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 C BOOL VALID BRANCH OK'

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
