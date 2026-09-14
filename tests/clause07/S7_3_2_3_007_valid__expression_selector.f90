! rule: S7.3.2.3-007
! covers: nonpolymorphic-expression-selector
! evidence: effect
program dynamic_expression_selector
    implicit none
    type :: node
        integer :: tag
    end type
    type(node) :: mold
    mold%tag = 0
    associate (value => node(71))
        if (.not. same_type_as(value, mold)) error stop 'expression-type'
        if (value%tag /= 71) error stop 'expression-payload'
    end associate
end program
