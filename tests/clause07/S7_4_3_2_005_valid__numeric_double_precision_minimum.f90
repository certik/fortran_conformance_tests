! rule: S7.4.3.2-005
! covers: double-precision-at-least-ten
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (precision(0.0d0) < 10) error stop 1
    call check(precision(0.0d0))
contains
    subroutine check(value)
        integer, intent(in) :: value
        if (value < 10) error stop 2
    end subroutine
end program numeric_literal_case
