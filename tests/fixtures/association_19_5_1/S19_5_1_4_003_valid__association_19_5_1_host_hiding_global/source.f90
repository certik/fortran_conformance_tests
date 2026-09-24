! rule: S19.5.1.4-003
! covers: use-associated-name-hides-host module-name-global-hides-host
! evidence: effect
! standard: f2023
! oracle-basis: standard
module association_provider_x
  implicit none
  integer :: x = 602
  integer :: wrong_x = 692
end module association_provider_x
module m
  implicit none
  integer :: value = 604
end module m
module wrong_m
  implicit none
  integer :: value = 694
end module wrong_m
program association_host_hiding_global
  implicit none
  integer :: x, m, use_seen, module_seen, checks
  x = 601
  m = 603
  use_seen = -11
  module_seen = -12
  checks = 0
  call read_use_name()
  call read_module_name()
  call expect_equal(use_seen, 602, 'use-associated name hides host')
  call expect_equal(x, 601, 'host x unchanged by use association')
  call expect_equal(module_seen, 604, 'module-name global hides host')
  call expect_equal(m, 603, 'host m unchanged by module-name')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST HIDING GLOBAL OK'
contains
  subroutine read_use_name()
    use association_provider_x, only: x, wrong_x
    implicit none
    use_seen = x
  end subroutine read_use_name
  subroutine read_module_name()
    use m, only: value
    implicit none
    module_seen = value
  end subroutine read_module_name
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ASSOCIATION-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program association_host_hiding_global
