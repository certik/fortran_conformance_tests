! rule: R902
! covers: expression-not-variable type-parameter-inquiry-boundary
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_variable_boundary_control
  implicit none
  integer :: x, len_value, checks
  character(len=3) :: c
  checks = 0
  c = 'abc'
  x = 7
  len_value = len(c)
  call expect_int(x, 7, 'ordinary variable repair for expression lhs')
  call expect_int(len_value, 3, 'ordinary variable repair for len inquiry')
  call expect_int(checks, 2, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS VARIABLE BOUNDARY CONTROL OK'
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
end program dataobj_variable_boundary_control
