! rule: S19.5.1.4-004
! covers: local-type-param-name-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_local_type_param
  implicit none
  integer, parameter :: x = 203
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 304, 'local-type-param-name-hides-host local value')
  call expect_equal(x, 203, 'local-type-param-name-hides-host host unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 LOCAL TYPE PARAM OK'
contains
  subroutine inner()
    implicit none
    type :: box(x)
      integer, len :: x = 304
      character(len=x) :: text
    end type box
    type(box) :: obj
    observed = len(obj%text)
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
end program association_local_type_param
