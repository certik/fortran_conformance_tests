! rule: S7.4.3.3-003
! covers: default-complex-kind default-real-component default-imaginary-component
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    complex :: z = (0.0, 0.0)
    if (kind(z) /= kind(0.0)) error stop 1
    call check(z%re)
    call check(z%im)
contains
    subroutine check(value)
        real, intent(in) :: value
        if (kind(value) /= kind(0.0)) error stop 2
    end subroutine
end program numeric_literal_case
