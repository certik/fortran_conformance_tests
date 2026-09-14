! rule: R609
! covers: extended-intrinsic-op
! evidence: positive-control
module r609_extended_unary_m
    implicit none
    type :: flag
        logical :: set
    end type flag
    interface operator (.not.)
        module procedure invert_flag
    end interface
contains
    logical function invert_flag(operand) result(value)
        type(flag), intent(in) :: operand
        value = .not. operand%set
    end function invert_flag
end module r609_extended_unary_m

program defined_intrinsic_unary
    use r609_extended_unary_m
    implicit none
    type(flag) :: operand
    logical :: result

    operand%set = .true.
    result = .not. operand
    if (merge(1, 0, result) /= 0) error stop 1
    operand%set = .false.
    result = .not. operand
    if (merge(1, 0, result) /= 1) error stop 2
end program defined_intrinsic_unary
