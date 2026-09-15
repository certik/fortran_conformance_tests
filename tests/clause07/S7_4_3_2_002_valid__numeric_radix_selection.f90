! rule: S7.4.3.2-002
! covers: radix-selection
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: k = selected_real_kind(p=10, r=37, radix=radix(0.0d0))
    real(k) :: z = 0.0_k
    if (k < 0) error stop 1
    if (kind(z) /= k) error stop 2
    if (precision(z) < 10) error stop 3
    if (range(z) < 37) error stop 4
    if (radix(z) /= radix(0.0d0)) error stop 5
end program numeric_literal_case
