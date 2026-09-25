! rule: R903
! covers: single-name-token not-designator-syntax
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_variable_name_token_control
  implicit none
  integer :: x, z, y, w, ios, checks
  character(len=32) :: input_one, input_two
  namelist /grp_one/ x
  namelist /grp_two/ z
  checks = 0
  x = -777
  z = -888
  y = -1
  w = -2
  input_one = '&grp_one x=64 /'
  input_two = '&grp_two z=74 /'
  read(input_one, nml=grp_one, iostat=ios)
  call expect_int(ios, 0, 'single name token namelist read status')
  call expect_int(x, 64, 'single variable-name token')
  read(input_two, nml=grp_two, iostat=ios)
  call expect_int(ios, 0, 'designator repair namelist read status')
  call expect_int(z, 74, 'simple name repair for designator syntax')
  call expect_int(checks, 4, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS VARIABLE NAME TOKEN CONTROL OK'
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
end program dataobj_variable_name_token_control
