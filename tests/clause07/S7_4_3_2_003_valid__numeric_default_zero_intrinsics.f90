! rule: S7.4.3.2-003
! covers: finite-intrinsic-arguments
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    real :: u, p, n
    data u, p, n /0.0, +0.0, -0.0/
    if (abs(p) /= u) error stop 1
    if (abs(n) /= u) error stop 2
    if (min(p,n) /= u) error stop 3
    if (min(n,p) /= u) error stop 4
    if (max(p,n) /= u) error stop 5
    if (max(n,p) /= u) error stop 6
    if (int(p) /= 0 .or. int(n) /= 0) error stop 7
    if (kind(int(p)) /= kind(0)) error stop 8
end program numeric_literal_case
