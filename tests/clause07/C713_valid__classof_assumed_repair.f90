! rule: C713
! covers: nonoptional-assumed
! evidence: positive-control
! standard: f2023
program c713_classof_assumed
    implicit none
    type :: packet(n)
        integer, len :: n
        character(n) :: text
    end type
contains
    subroutine inspect(seed)
        class(packet(n=*)), intent(in) :: seed
        classof(seed), allocatable :: copy
    end subroutine
end program
