! rule: S19.5.1.4-004
! covers: local-dummy-arg-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_dummy
  implicit none
  integer :: x, actual, observed, checks
  x = 213
  actual = 313
  observed = -11
  checks = 0
  call inner(actual)
  call expect_equal(observed, 314, 'dummy argument local value')
  call expect_equal(actual, 314, 'actual changed through dummy')
  call expect_equal(x, 213, 'host x unchanged')
  call expect_equal(checks, 3, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL DUMMY OK'
contains
  subroutine inner(x)
    implicit none
    integer, intent(inout) :: x
    x = 314
    observed = x
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
end program association_local_dummy
