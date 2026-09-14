! rule: S6.2.6-001
! covers: left-parenthesis right-parenthesis
! evidence: positive-control
program delimiter_parentheses_admission
    implicit none
    integer :: left, right, value

    left = 2
    right = 3
    value = (left + right) * 4
    if (value /= 20) error stop 1
end program delimiter_parentheses_admission
