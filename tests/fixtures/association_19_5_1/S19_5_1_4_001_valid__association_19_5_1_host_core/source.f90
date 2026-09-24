! rule: S19.5.1.4-001
! covers:
!   internal-subprogram-host-instance-access
!   host-variable-previously-declared
!   host-nonvariable-previously-defined
!   host-identifier-and-attributes-preserved
! evidence: effect
! standard: f2023
! oracle-basis: standard
program association_host_core
  implicit none
  type :: box
    integer :: v
  end type box
  interface g
    procedure g_int
  end interface g
  integer, parameter :: p = 3
  integer, target :: t
  integer :: x, y, observed, observed_y, generic_seen, type_seen, extent_seen, pointer_seen, checks
  integer, pointer :: q
  x = 1
  y = 43
  t = 5
  observed = -11
  observed_y = -16
  generic_seen = -12
  type_seen = -13
  extent_seen = -14
  pointer_seen = -15
  checks = 0
  call inner()
  call expect_equal(x, 42, 'host instance variable changed')
  call expect_equal(observed, 42, 'host variable previously declared')
  call expect_equal(observed_y, 43, 'separate host variable previously declared')
  call expect_equal(type_seen, 64, 'host type nonvariable previously defined')
  call expect_equal(generic_seen, 77, 'host generic nonvariable previously defined')
  call expect_equal(extent_seen, 3, 'host parameter attribute preserved')
  call expect_equal(pointer_seen, 5, 'host target attribute preserved')
  call expect_equal(checks, 7, 'check count before completion')
  write(*,'(a)') 'ASSOCIATION 19.5.1 HOST CORE OK'
contains
  integer function g_int(n)
    integer, intent(in) :: n
    g_int = 76 + n
  end function g_int
  subroutine inner()
    implicit none
    type(box) :: local_box
    integer :: arr(p)
    x = 42
    observed = x
    observed_y = y
    local_box = box(64)
    type_seen = local_box%v
    generic_seen = g(1)
    extent_seen = size(arr)
    q => t
    pointer_seen = q
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
end program association_host_core
