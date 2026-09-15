! rule: S7.4.3.3-004
! covers: greater-precision-second
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: k = kind((0.0,0.0d0))
    complex(k) :: z = (0.0,0.0d0)
    if (kind((0.0,0.0d0)) /= kind(0.0d0)) error stop 1
    if (kind(z%re) /= k .or. kind(z%im) /= k) error stop 2
end program numeric_literal_case
