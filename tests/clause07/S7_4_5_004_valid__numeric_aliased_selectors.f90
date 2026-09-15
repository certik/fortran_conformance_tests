! rule: S7.4.5-004
! covers: coincident-selectors
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: first = kind(.false.), second = first
    if (kind(.true._first) /= kind(.false._second)) error stop 1
    call first_kind(.true._first, .true.)
    call first_kind(.false._first, .false.)
    call second_kind(.true._second, .true.)
    call second_kind(.false._second, .false.)
contains
    subroutine first_kind(value, expected)
        logical(first), intent(in) :: value, expected
        if (value .neqv. expected) error stop 2
    end subroutine
    subroutine second_kind(value, expected)
        logical(second), intent(in) :: value, expected
        if (value .neqv. expected) error stop 3
    end subroutine
end program numeric_literal_case
