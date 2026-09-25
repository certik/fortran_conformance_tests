! rule: S9.2-002
! covers: defined-variable-reference defined-pointer-target-reference definition-event-source
! evidence: effect
! standard: f2023
! oracle-basis: standard
program dataobj_defined_references
  implicit none
  integer, target :: t
  integer, pointer :: p
  integer :: x, checks
  character(len=2) :: buffer
  checks = 0
  x = 51
  call expect_int(x, 51, 'defined variable reference after assignment')
  t = 61
  p => t
  call expect_int(p, 61, 'defined target reference through pointer')
  buffer = '##'
  write(buffer, '(i2)') 73
  call expect_char(buffer, '73', 'internal write definition event')
  call expect_int(checks, 3, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS DEFINED REFERENCES OK'
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
end program dataobj_defined_references
