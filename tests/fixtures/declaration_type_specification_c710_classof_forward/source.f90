program c710_classof_prior
    implicit none
    type :: packet(n)
        integer, len :: n
        character(n) :: text
    end type
    classof(seed), allocatable :: copy
    type(packet(3)) :: seed
    seed%text = 'abc'
    if (seed%text /= 'abc') error stop 'value'
end program
