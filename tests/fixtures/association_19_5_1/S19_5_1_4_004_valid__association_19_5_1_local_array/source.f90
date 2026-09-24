! rule: S19.5.1.4-004
! covers: local-array-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_array
  implicit none
  integer :: abs, x, observed, checks
  x = 208
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 309, 'local-array-name-hides-host local value')
  call expect_equal(x, 208, 'local-array-name-hides-host host unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL ARRAY OK'
contains
  subroutine inner()
    implicit none
    integer :: x
    dimension x(1)
    x = [309]
    observed = x(1)
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
end program association_local_array
