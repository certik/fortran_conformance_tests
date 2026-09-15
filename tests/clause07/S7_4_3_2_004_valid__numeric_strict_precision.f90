! rule: S7.4.3.2-004
! covers: strict-decimal-precision
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (precision(0.0d0) <= precision(0.0)) error stop 1
end program numeric_literal_case
