program c712_intrinsic
    implicit none
    type :: payload
        integer :: code
    end type
    integer :: seed = 3
    classof(seed), allocatable :: copy
end program
