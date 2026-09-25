! rule: C907
! covers: integer-type-admission
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_integer_type_admission
  implicit none
  integer, allocatable :: a
  integer :: stat_value, other_stat, checks
  checks = 0
  stat_value = -777
  other_stat = -888
  allocate(a, stat=stat_value)
  call expect_int(stat_value, 0, 'integer STAT variable type admission')
  call expect_int(checks, 1, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS INTEGER TYPE ADMISSION OK'
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
end program dataobj_integer_type_admission
