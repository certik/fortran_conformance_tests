! rule: S7.4.5-003
! covers: omitted-selector-kind explicit-default-agreement
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    logical :: a = .true., b = .false.
    if (kind(a) /= kind(.false.)) error stop 1
    call check(a, .true.)
    call check(b, .false.)
contains
    subroutine check(value, expected)
        logical(kind(.false.)), intent(in) :: value, expected
        if (kind(value) /= kind(.false.)) error stop 2
        if (value .neqv. expected) error stop 3
    end subroutine
end program numeric_literal_case
