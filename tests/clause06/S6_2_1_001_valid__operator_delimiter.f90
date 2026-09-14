! rule: S6.2.1-001
! covers: operator delimiter
! evidence: positive-control
program token_operator_delimiter_admission
    implicit none
    integer :: left, right, value

    left = 2
    right = 3
    value = (left + right) * 4
    if (value /= 20) error stop 1
end program token_operator_delimiter_admission
