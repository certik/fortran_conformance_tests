! rule: S18.2.3.2-003
! covers: c-associated-first-argument-scalar-c-pointer c-associated-second-argument-same-type
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_associated_argument_controls
  use, intrinsic :: iso_c_binding, only: c_int, c_ptr, c_funptr, c_null_ptr, c_null_funptr, c_loc, c_associated
  implicit none
  integer(c_int), target :: value
  type(c_ptr) :: p1, p2
  type(c_funptr) :: fp
  integer(c_int) :: checks
  checks = 0_c_int
  value = 77_c_int
  p1 = c_loc(value)
  p2 = c_null_ptr
  fp = c_null_funptr
  call expect_logical(c_associated(p1), .true., 'scalar C_PTR first argument')
  call expect_logical(c_associated(fp), .false., 'scalar C_FUNPTR first argument')
  call expect_logical(c_associated(p2, p1), .false., 'same TYPE(C_PTR) second argument')
  call expect_int(checks, 3_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.3.2 C ASSOCIATED ARGUMENT CONTROLS OK'

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
