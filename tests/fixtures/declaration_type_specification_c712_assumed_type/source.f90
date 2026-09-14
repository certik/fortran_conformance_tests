program c712_assumed_type
    implicit none
contains
    subroutine inspect(seed)
        type(*), intent(in) :: seed
        classof(seed), allocatable :: copy
    end subroutine
end program
