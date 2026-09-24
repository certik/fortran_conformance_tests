! rule: S19.5.1.4-004
! covers: local-procedure-pointer-external-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_proc_pointer
  implicit none
  abstract interface
    integer function intfun()
    end function intfun
  end interface
  procedure(intfun), pointer :: x
  integer :: observed, checks
  x => host_target
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 324, 'local procedure pointer value')
  call expect_equal(x(), 223, 'host procedure pointer unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL PROC POINTER OK'
contains
  integer function host_target()
    implicit none
    host_target = 223
  end function host_target
  integer function local_target()
    implicit none
    local_target = 324
  end function local_target
  subroutine inner()
    implicit none
    procedure(intfun), pointer :: x
    x => local_target
    observed = x()
  end subroutine inner
  subroutine expect_equal(observed_value, expected, label)
    implicit none
    integer, intent(in) :: observed_value, expected
    character(len=*), intent(in) :: label
    if (observed_value /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed_value, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_local_proc_pointer
