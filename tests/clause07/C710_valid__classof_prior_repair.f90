! rule: C710
! covers: classof-prior-type-parameters
! evidence: positive-control
! standard: f2023
program c710_classof_prior
    implicit none
    type :: packet(n)
        integer, len :: n
        character(n) :: text
    end type
    type(packet(3)) :: seed
    classof(seed), allocatable :: copy
    seed%text = 'abc'
    if (seed%text /= 'abc') error stop 'value'
end program
