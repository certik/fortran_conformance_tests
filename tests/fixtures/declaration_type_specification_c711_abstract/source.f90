program c711_abstract
    implicit none
    type, abstract :: root
        integer :: code
    end type
    class(root), allocatable :: seed
    typeof(seed), allocatable :: copy
end program
