! rule: S19.5.1.4-003
! covers: external-global-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_external_global_hide
  implicit none
  integer :: x, observed, checks
  x = 605
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 606, 'external global name hides host')
  call expect_equal(x, 605, 'host x unchanged by external global')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 EXTERNAL GLOBAL HIDE OK'
contains
  subroutine inner()
    implicit none
    integer, external :: x
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
end program association_external_global_hide
integer function x()
  implicit none
  x = 606
end function x
