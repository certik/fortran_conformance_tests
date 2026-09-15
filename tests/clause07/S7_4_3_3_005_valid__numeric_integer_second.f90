! rule: S7.4.3.3-005
! covers: real-first-integer-second
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: ik = selected_int_kind(18)
    if (kind((0.0d0,0)) /= kind(0.0d0)) error stop 1
    call check((0.0d0,0))
    if (kind((0.0d0,0_ik)) /= kind(0.0d0)) error stop 2
    call check((0.0d0,0_ik))
contains
    subroutine check(value)
        complex(kind(0.0d0)), intent(in) :: value
        if (kind(value%re) /= kind(0.0d0)) error stop 20
        if (kind(value%im) /= kind(0.0d0)) error stop 21
    end subroutine
end program numeric_literal_case
