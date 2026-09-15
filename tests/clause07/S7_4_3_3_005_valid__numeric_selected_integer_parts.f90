! rule: S7.4.3.3-005
! covers: both-selected-integers
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: ik = selected_int_kind(18)
    if (kind((0_ik,0)) /= kind(0.0)) error stop 1
    call check((0_ik,0))
    if (kind((0,0_ik)) /= kind(0.0)) error stop 2
    call check((0,0_ik))
    if (kind((0_ik,0_ik)) /= kind(0.0)) error stop 3
    call check((0_ik,0_ik))
contains
    subroutine check(value)
        complex(kind(0.0)), intent(in) :: value
        if (kind(value%re) /= kind(0.0)) error stop 20
        if (kind(value%im) /= kind(0.0)) error stop 21
    end subroutine
end program numeric_literal_case
