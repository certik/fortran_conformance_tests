! rule: S18.2.3.2-005
! covers: c-associated-absent-null-false c-associated-absent-nonnull-true
! evidence: effect
! standard: f2023
! oracle-basis: standard
program iso_c_binding_c_associated_values
  use, intrinsic :: iso_c_binding, only: c_int, c_ptr, c_null_ptr, c_loc, c_associated
  implicit none
  integer(c_int), target :: first, second
  type(c_ptr) :: p_first, p_first_again, p_second, p_null
  logical :: result
  integer(c_int) :: checks
  checks = 0_c_int
  first = 91_c_int
  second = 92_c_int
  p_first = c_loc(first)
  p_first_again = c_loc(first)
  p_second = c_loc(second)
  p_null = c_null_ptr
  result = .true.
  result = c_associated(p_null)
  call expect_logical(result, .false., 'absent second null false')
  result = .false.
  result = c_associated(p_first)
  call expect_logical(result, .true., 'absent second nonnull true')
  result = .true.
  result = c_associated(p_null, p_first)
  call expect_logical(result, .false., 'present second first null false')
  result = .false.
  result = c_associated(p_first, p_first_again)
  call expect_logical(result, .true., 'present second equal true')
  result = .true.
  result = c_associated(p_first, p_second)
  call expect_logical(result, .false., 'present second unequal false')
  call expect_int(checks, 5_c_int, 'check count')
  write(*,'(a)') 'ISO_C_BINDING 18.2.3.2 C ASSOCIATED VALUES OK'

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
