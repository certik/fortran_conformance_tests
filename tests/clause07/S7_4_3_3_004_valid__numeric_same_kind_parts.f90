! rule: S7.4.3.3-004
! covers: same-kind-parts
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: kr = kind(0.0), kd = kind(0.0d0)
    if (kind((0.0_kr,0.0_kr)) /= kr) error stop 1
    if (kind((0.0_kd,0.0_kd)) /= kd) error stop 2
end program numeric_literal_case
