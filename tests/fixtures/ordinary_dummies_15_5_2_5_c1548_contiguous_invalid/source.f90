! rule: C1548
! covers: nonpointer-discontiguous-dummy-no-contiguous
! evidence: effect
! standard: f2023
program c1548_contiguous_invalid
  implicit none
  integer, volatile :: a(3) = [10, 20, 30]
  call bad(a(3:1:-2))
contains
  subroutine bad(x)
    integer, volatile, contiguous :: x(:)
    if (x(1) /= 30) error stop 1
  end subroutine
end program
