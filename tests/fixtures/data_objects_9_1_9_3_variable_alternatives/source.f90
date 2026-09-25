! rule: R902
! covers: designator-variable function-reference-variable
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
module dataobj_r902_pointer_m
  implicit none
  integer, target, save :: target_value = -101
contains
  function ip() result(p)
    integer, pointer :: p
    p => target_value
  end function
end module dataobj_r902_pointer_m
program dataobj_variable_alternatives
  use dataobj_r902_pointer_m
  implicit none
  integer :: x, checks
  checks = 0
  x = 11
  call expect_int(x, 11, 'designator variable assignment')
  ip() = 23
  call expect_int(target_value, 23, 'function reference variable assignment')
  call expect_int(checks, 2, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS VARIABLE ALTERNATIVES OK'
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
end program dataobj_variable_alternatives
