! rule: S15.1-002
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module argument_association_access_m
  implicit none
contains
  subroutine bump(x)
    integer, intent(inout) :: x
    x = x + 31
  end subroutine
  subroutine leave_sentinel(x)
    integer, intent(inout) :: x
    x = x
  end subroutine
end module
program argument_association_access
  use argument_association_access_m
  implicit none
  integer :: actual
  actual = 11
  call bump(actual)
  if (actual /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.1 ARGUMENT ASSOCIATION ACCESS OK'
end program
