! rule: C903
! covers: ordinary-variable-name
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_c903_ordinary_variable_name
  implicit none
  integer :: ordinary, other, ios, checks
  character(len=32) :: input
  namelist /grp/ ordinary
  checks = 0
  ordinary = -909
  other = -1
  input = '&grp ordinary=71 /'
  read(input, nml=grp, iostat=ios)
  call expect_int(ios, 0, 'ordinary variable-name namelist status')
  call expect_int(ordinary, 71, 'ordinary variable-name value')
  call expect_int(checks, 2, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS C903 ORDINARY VARIABLE NAME OK'
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
end program dataobj_c903_ordinary_variable_name
