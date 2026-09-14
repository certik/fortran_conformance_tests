! rule: S7.3.2.3-008
! covers: derived-declared-identity
! evidence: effect
program dynamic_nonpolymorphic_derived
    implicit none
    type :: alpha
        integer :: tag
    end type
    type :: beta
        integer :: tag
    end type
    type(alpha) :: first, second
    type(beta) :: other
    first%tag = 17
    second%tag = 19
    other%tag = 23
    if (.not. same_type_as(first, second)) error stop 'same-definition'
    if (same_type_as(first, other)) error stop 'different-definitions'
    if (first%tag /= 17) error stop 'first-payload'
    if (second%tag /= 19) error stop 'second-payload'
    if (other%tag /= 23) error stop 'other-payload'
end program
