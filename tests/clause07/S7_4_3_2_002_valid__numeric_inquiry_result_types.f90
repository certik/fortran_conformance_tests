! rule: S7.4.3.2-002
! covers: default-integer-inquiry-results
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (kind(kind(0.0)) /= kind(0)) error stop 1
    call integer_result(kind(0.0))
    if (kind(kind(0.0d0)) /= kind(0)) error stop 2
    call integer_result(kind(0.0d0))
    if (kind(precision(0.0)) /= kind(0)) error stop 3
    call integer_result(precision(0.0))
    if (kind(precision(0.0d0)) /= kind(0)) error stop 4
    call integer_result(precision(0.0d0))
    if (kind(range(0.0)) /= kind(0)) error stop 5
    call integer_result(range(0.0))
    if (kind(range(0.0d0)) /= kind(0)) error stop 6
    call integer_result(range(0.0d0))
    if (kind(radix(0.0)) /= kind(0)) error stop 7
    call integer_result(radix(0.0))
    if (kind(radix(0.0d0)) /= kind(0)) error stop 8
    call integer_result(radix(0.0d0))
    if (kind(selected_real_kind(p=10)) /= kind(0)) error stop 9
    call integer_result(selected_real_kind(p=10))
    if (kind(selected_real_kind(r=37)) /= kind(0)) error stop 10
    call integer_result(selected_real_kind(r=37))
    if (kind(selected_real_kind(p=10, r=37, radix=radix(0.0d0))) /= kind(0)) error stop 11
    call integer_result(selected_real_kind(p=10, r=37, radix=radix(0.0d0)))
contains
    subroutine integer_result(value)
        integer, intent(in) :: value
        if (kind(value) /= kind(0)) error stop 90
    end subroutine
end program numeric_literal_case
