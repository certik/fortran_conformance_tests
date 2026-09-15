! rule: S7.4.3.2-002
! covers: precision-selection
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: k = selected_real_kind(p=10)
    real(k) :: z = 0.0_k
    if (k < 0) error stop 1
    if (kind(z) /= k) error stop 2
    if (precision(z) < 10) error stop 3
end program numeric_literal_case
