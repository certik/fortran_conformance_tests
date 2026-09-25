! rule: C905
! covers: character-type-admission
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_character_type_admission
  implicit none
  character(len=5) :: buffer, other_buffer
  integer :: checks
  checks = 0
  buffer = '#####'
  other_buffer = '?????'
  write(buffer, '(a)') 'abc'
  call expect_int(len(buffer), 5, 'character variable length')
  call expect_char(buffer(1:3), 'abc', 'character variable internal write')
  call expect_int(checks, 2, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS CHARACTER TYPE ADMISSION OK'
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
end program dataobj_character_type_admission
