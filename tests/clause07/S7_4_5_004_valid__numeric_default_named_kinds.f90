! rule: S7.4.5-004
! covers: default-named-true default-named-false
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: lk = kind(.false.)
    if (kind(.true._lk) /= lk) error stop 1
    if (kind(.false._lk) /= lk) error stop 2
    call check(.true._lk, .true.)
    call check(.false._lk, .false.)
contains
    subroutine check(value, expected)
        logical(lk), intent(in) :: value, expected
        if (value .neqv. expected) error stop 3
    end subroutine
end program numeric_literal_case
