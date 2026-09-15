! rule: S7.4.3.3-002
! covers: default-real-correspondence real-component-kind imaginary-component-kind kind-inquiry
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    integer, parameter :: k = kind(0.0)
    complex(k) :: z = (0.0_k, 0.0_k)
    if (kind(z) /= k) error stop 1
    if (kind(z%re) /= k .or. kind(z%im) /= k) error stop 2
    if (kind(real(z)) /= k .or. kind(aimag(z)) /= k) error stop 3
    if (kind(kind(z)) /= kind(0)) error stop 4
    call real_component(z%re)
    call real_component(z%im)
    call integer_result(kind(z))
contains
    subroutine real_component(value)
        real(k), intent(in) :: value
        if (kind(value) /= k) error stop 5
    end subroutine
    subroutine integer_result(value)
        integer, intent(in) :: value
        if (value /= k) error stop 6
    end subroutine
end program numeric_literal_case
