! rule: C902
! covers: data-pointer-result-admission nonpointer-result-excluded procedure-pointer-result-excluded
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
module dataobj_c902_pointer_m
  implicit none
  integer, target, save :: admit_target = -1, nonptr_target = -2, proc_target = -3
contains
  function p_admit() result(p)
    integer, pointer :: p
    p => admit_target
  end function
  function p_nonptr_repair() result(p)
    integer, pointer :: p
    p => nonptr_target
  end function
  function p_proc_repair() result(p)
    integer, pointer :: p
    p => proc_target
  end function
end module dataobj_c902_pointer_m
program dataobj_c902_data_pointer_controls
  use dataobj_c902_pointer_m
  implicit none
  integer :: checks
  checks = 0
  p_admit() = 31
  call expect_int(admit_target, 31, 'data pointer function result admission')
  p_nonptr_repair() = 41
  call expect_int(nonptr_target, 41, 'data pointer repair for nonpointer result')
  p_proc_repair() = 51
  call expect_int(proc_target, 51, 'data pointer repair for procedure pointer result')
  call expect_int(checks, 3, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS C902 DATA POINTER CONTROLS OK'
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
end program dataobj_c902_data_pointer_controls
