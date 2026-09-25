! rule: C1549
! covers: array-pointer-volatile-noncontiguous-dummy-form-restriction
! evidence: effect
! standard: f2023
program c1549_volatile_invalid
  implicit none
  integer, target :: a(5) = [10, 20, 30, 40, 50]
  integer, pointer, volatile :: p(:)
  p => a(1:5:2)
  call bad(p)
contains
  subroutine bad(x)
    integer, volatile :: x(3)
    if (x(1) /= 10) error stop 1
  end subroutine
end program
