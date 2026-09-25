! rule: S18.2.3.1-001
! covers: iso-c-binding-procedure-names-generic
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_associated_generic
  use, intrinsic :: iso_c_binding, only: c_int, c_null_ptr, c_null_funptr, c_funloc, c_associated
  implicit none
  integer(c_int) :: checks
  checks = 0_c_int
  call expect_logical(c_associated(c_null_ptr), .false., 'C_ASSOCIATED generic resolves C_PTR')
  call expect_logical(c_associated(c_funloc(local_function)), .true., 'C_ASSOCIATED generic resolves C_FUNPTR')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.3.1 C ASSOCIATED GENERIC OK'
contains
  integer(c_int) function local_function() bind(c)
    local_function = 1_c_int
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
