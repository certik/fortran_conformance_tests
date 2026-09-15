! rule: S7.4.3.3-005
! covers: both-default-integers
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (kind((0,0)) /= kind(0.0)) error stop 1
    call check((0,0))
contains
    subroutine check(value)
        complex(kind(0.0)), intent(in) :: value
        if (kind(value%re) /= kind(0.0)) error stop 20
        if (kind(value%im) /= kind(0.0)) error stop 21
    end subroutine
end program numeric_literal_case
