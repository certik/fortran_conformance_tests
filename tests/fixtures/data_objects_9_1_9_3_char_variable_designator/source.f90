! rule: R905
! covers: designator-character-variable
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_char_variable_designator
  implicit none
  character(len=4) :: buffer, other_buffer
  integer :: checks
  checks = 0
  buffer = '####'
  other_buffer = '????'
  write(buffer, '(a)') 'ok'
  call expect_char(buffer(1:2), 'ok', 'character designator internal file')
  call expect_int(checks, 1, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS CHAR VARIABLE DESIGNATOR OK'
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
end program dataobj_char_variable_designator
