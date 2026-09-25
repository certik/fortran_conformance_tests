! rule: C1549
! covers: array-pointer-noncontiguous-dummy-no-contiguous
! evidence: effect
! standard: f2023
program c1549_contiguous_invalid
  implicit none
  integer, target :: a(5) = [10, 20, 30, 40, 50]
  integer, pointer, volatile :: p(:)
  p => a(1:5:2)
  call bad(p)
contains
  subroutine bad(x)
    integer, volatile, contiguous :: x(:)
    if (x(1) /= 10) error stop 1
  end subroutine
end program
