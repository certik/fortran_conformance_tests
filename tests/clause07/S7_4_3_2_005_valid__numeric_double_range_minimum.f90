! rule: S7.4.3.2-005
! covers: double-range-at-least-thirty-seven
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (range(0.0d0) < 37) error stop 1
    call check(range(0.0d0))
contains
    subroutine check(value)
        integer, intent(in) :: value
        if (value < 37) error stop 2
    end subroutine
end program numeric_literal_case
