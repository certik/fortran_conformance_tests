! rule: S10.2.1.3-002
! covers: independent-operands
! evidence: positive-control
! F2023 10.2.1.3 p1: no interfering side effects and no call-order assertion.
program s10_2_1_3_002_valid
    implicit none
    integer :: a(3), position, input
    position = 2
    input = 37
    a = [2, 5, 9]
    a(lhs_index()) = rhs_value()
    if (any(a /= [2, 37, 9])) error stop 'independent-operands'
    if (position /= 2 .or. input /= 37) error stop 'inputs-unchanged'
contains
    integer function lhs_index()
        lhs_index = position
    end function
    integer function rhs_value()
        rhs_value = input
    end function
end program
