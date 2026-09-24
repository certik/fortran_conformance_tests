! rule: S19.5.1.4-004
! covers: local-data-initialized-variable-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_data_initialized
  implicit none
  integer :: abs, x, observed, checks
  x = 209
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 310, 'local-data-initialized-variable-hides-host local value')
  call expect_equal(x, 209, 'local-data-initialized-variable-hides-host host unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL DATA INITIALIZED OK'
contains
  subroutine inner()
    implicit none
    integer :: x
    data x /310/
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
end program association_local_data_initialized
