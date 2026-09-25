! rule: C1548
! covers: nonpointer-async-discontiguous-dummy-shape-restriction
! evidence: effect
! standard: f2023
program c1548_asynchronous_invalid
  implicit none
  integer, asynchronous :: a(3) = [10, 20, 30]
  call bad(a(3:1:-2))
contains
  subroutine bad(x)
    integer, asynchronous :: x(2)
    if (x(1) /= 30) error stop 1
  end subroutine
end program
