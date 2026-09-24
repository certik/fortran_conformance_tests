! rule: S19.5.1.4-004
! covers: local-generic-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_generic
  implicit none
  interface x
    integer function host_x(n)
      integer, intent(in) :: n
    end function host_x
  end interface
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 318, 'local generic value')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL GENERIC OK'
contains
  subroutine inner()
    implicit none
    interface x
      integer function local_x(n)
        integer, intent(in) :: n
      end function local_x
    end interface
    observed = x(0)
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
end program association_local_generic
integer function host_x(n)
  implicit none
  integer, intent(in) :: n
  host_x = 217 + n
end function host_x
integer function local_x(n)
  implicit none
  integer, intent(in) :: n
  local_x = 318 + n
end function local_x
