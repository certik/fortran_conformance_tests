! rule: S19.5.1.4-001
! covers: derived-type-host-access
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_host_derived_type
  implicit none
  integer, parameter :: n = 3
  integer, parameter :: wrong_n = 5
  integer :: observed, checks
  observed = -11
  checks = 0
  call inner()
  call expect_equal(observed, 3, 'derived type definition used host parameter')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST DERIVED TYPE OK'
contains
  subroutine inner()
    implicit none
    type :: local_box
      character(len=n) :: text
    end type local_box
    type(local_box) :: obj
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
end program association_host_derived_type
