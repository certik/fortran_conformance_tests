! rule: S19.5.1.4-004
! covers: local-result-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_result
  implicit none
  integer :: x, observed, checks
  x = 215
  observed = -11
  checks = 0
  observed = f()
  call expect_equal(observed, 316, 'result name local value')
  call expect_equal(x, 215, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL RESULT OK'
contains
  integer function f() result(x)
    implicit none
    x = 316
  end function f
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
end program association_local_result
