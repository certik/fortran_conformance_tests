! rule: S19.5.1.4-001
! covers: module-subprogram-host-access
! evidence: effect
! standard: f2023
! oracle-basis: standard
module association_host_module_proc_mod
  implicit none
  integer :: x = 42
contains
  subroutine read_module_host(observed)
    implicit none
    integer, intent(out) :: observed
    observed = x
  end subroutine read_module_host
end module association_host_module_proc_mod
program association_host_module_proc
  use association_host_module_proc_mod, only: read_module_host
  implicit none
  integer :: observed, checks
  observed = -11
  checks = 0
  call read_module_host(observed)
  call expect_equal(observed, 42, 'module procedure host access')
  call expect_equal(checks, 1, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST MODULE PROC OK'
contains
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
end program association_host_module_proc
