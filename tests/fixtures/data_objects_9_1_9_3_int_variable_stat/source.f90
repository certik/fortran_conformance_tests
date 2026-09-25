! rule: R907
! covers: designator-integer-variable function-reference-integer-variable
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
module dataobj_r907_stat_m
  implicit none
  integer, target, save :: stat_target = -1, other_stat_target = -2
contains
  function stat_ptr() result(p)
    integer, pointer :: p
    p => stat_target
  end function
  function other_stat_ptr() result(p)
    integer, pointer :: p
    p => other_stat_target
  end function
end module dataobj_r907_stat_m
program dataobj_int_variable_stat
  use dataobj_r907_stat_m
  implicit none
  integer, allocatable :: a, b
  integer :: s, other_s, checks
  checks = 0
  s = -777
  other_s = -888
  allocate(a, stat=s)
  call expect_int(s, 0, 'integer designator STAT variable')
  stat_target = -999
  allocate(b, stat=stat_ptr())
  call expect_int(stat_target, 0, 'integer function-reference STAT variable')
  call expect_int(checks, 2, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS INT VARIABLE STAT OK'
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
end program dataobj_int_variable_stat
