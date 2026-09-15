! rule: S7.4.3.2-006
! covers: named-kind
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: kr = kind(0.0), kd = kind(0.0d0)
    if (kind(0.0_kr) /= kr) error stop 1
    if (kind(0.0e0_kr) /= kr) error stop 2
    if (kind(0e0_kr) /= kr) error stop 3
    if (kind(0.0_kd) /= kd) error stop 4
    if (kind(0.0e0_kd) /= kd) error stop 5
    if (kind(0e0_kd) /= kd) error stop 6
end program numeric_literal_case
