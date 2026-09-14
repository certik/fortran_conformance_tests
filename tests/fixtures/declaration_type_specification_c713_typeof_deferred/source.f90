program c713_typeof_deferred
    implicit none
contains
    subroutine inspect(seed)
        character(:), allocatable, optional, intent(in) :: seed
        typeof(seed), allocatable :: copy
    end subroutine
end program
