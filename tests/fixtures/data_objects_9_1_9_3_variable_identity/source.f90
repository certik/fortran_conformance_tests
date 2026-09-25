! rule: S9.2-001
! covers: designator-denotes-object function-reference-denotes-target associated-pointer-required
! evidence: effect
! standard: f2023
! oracle-basis: standard
module dataobj_identity_pointer_m
  implicit none
  integer, target, save :: target_a = -1, first_selected = -2, second_selected = 53
  logical, save :: choose_first = .true.
contains
  function ip() result(p)
    integer, pointer :: p
    p => target_a
  end function
  function selected_ptr() result(p)
    integer, pointer :: p
    if (choose_first) then
      p => first_selected
    else
      p => second_selected
    end if
  end function
end module dataobj_identity_pointer_m
program dataobj_variable_identity
  use dataobj_identity_pointer_m
  implicit none
  integer :: x, checks
  checks = 0
  x = 41
  call expect_int(x, 41, 'designator denotes the assigned object')
  target_a = -5
  ip() = 42
  call expect_int(target_a, 42, 'function reference denotes pointer target')
  choose_first = .true.
  selected_ptr() = 52
  call expect_int(first_selected, 52, 'associated pointer selected first target')
  call expect_int(checks, 3, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS VARIABLE IDENTITY OK'
contains
  subroutine expect_true(ok, label)
    logical, intent(in) :: ok
    character(len=*), intent(in) :: label
    if (.not. ok) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'DATAOBJ-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char(observed, expected, label)
    character(len=*), intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-LEN', label
      error stop
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-CHAR', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program dataobj_variable_identity
