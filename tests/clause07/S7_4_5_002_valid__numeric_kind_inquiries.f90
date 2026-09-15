! rule: S7.4.5-002
! covers: kind-inquiry default-integer-inquiry-result
! evidence: effect
! standard: f2023
program numeric_literal_case
    use iso_fortran_env, only: logical_kinds
    implicit none
    integer, parameter :: first = logical_kinds(1), lk = kind(.false.)
    logical :: a = .false.
    logical(first) :: b = .true._first
    if (kind(a) /= lk) error stop 1
    if (kind(b) /= first) error stop 2
    if (kind(kind(a)) /= kind(0)) error stop 3
    if (kind(kind(b)) /= kind(0)) error stop 4
    call integer_result(kind(a))
    call integer_result(kind(b))
contains
    subroutine integer_result(value)
        integer, intent(in) :: value
        if (kind(value) /= kind(0)) error stop 90
    end subroutine
end program numeric_literal_case
