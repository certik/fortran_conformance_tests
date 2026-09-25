! rule: S18.2.2-014
! covers: c-null-ptr-type-and-value c-null-funptr-type-and-value
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_null_pointer_constants
  use, intrinsic :: iso_c_binding, only: c_int, c_ptr, c_funptr, c_null_ptr, c_null_funptr, c_loc, c_funloc, c_associated
  implicit none
  integer(c_int), target :: target
  type(c_ptr) :: p
  type(c_funptr) :: fp
  integer(c_int) :: checks
  checks = 0_c_int
  target = 77_c_int
  p = c_loc(target)
  fp = c_funloc(local_function)
  p = c_null_ptr
  fp = c_null_funptr
  call expect_logical(c_associated(p), .false., 'C_NULL_PTR null value')
  call expect_logical(c_associated(fp), .false., 'C_NULL_FUNPTR null value')
  call expect_int(checks, 2_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.2 NULL POINTER CONSTANTS OK'
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
