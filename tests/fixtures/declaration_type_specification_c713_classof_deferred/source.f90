program c713_classof_deferred
    implicit none
    type :: packet(n)
        integer, len :: n
        character(n) :: text
    end type
contains
    subroutine inspect(seed)
        class(packet(n=:)), allocatable, optional, intent(in) :: seed
        classof(seed), allocatable :: copy
    end subroutine
end program
