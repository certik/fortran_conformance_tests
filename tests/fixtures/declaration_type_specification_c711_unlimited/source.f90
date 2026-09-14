program c711_unlimited
    implicit none
    type :: root
        integer :: code
    end type
    class(*), allocatable :: seed
    typeof(seed), allocatable :: copy
end program
