! rule: S19.5.1.4-004
! covers: local-interface-entity-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_interface_entity
  implicit none
  integer :: x, observed, checks
  x = 219
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 320, 'local interface entity value')
  call expect_equal(x, 219, 'host x unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL INTERFACE ENTITY OK'
contains
  subroutine inner()
    implicit none
    interface
      integer function x()
      end function x
    end interface
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
end program association_local_interface_entity
integer function x()
  implicit none
  x = 320
end function x
