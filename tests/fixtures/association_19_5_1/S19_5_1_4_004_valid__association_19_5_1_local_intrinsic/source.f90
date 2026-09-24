! rule: S19.5.1.4-004
! covers: local-intrinsic-procedure-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_intrinsic
  implicit none
  integer :: abs, x, observed, checks
  x = 217
  abs = 39
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 3, 'local intrinsic abs value')
  call expect_equal(x, 217, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL INTRINSIC OK'
contains
  subroutine inner()
    implicit none
    intrinsic :: abs
    observed = abs(-3)
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
end program association_local_intrinsic
