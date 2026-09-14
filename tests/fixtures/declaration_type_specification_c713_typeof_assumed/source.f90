program c713_typeof_assumed
    implicit none
contains
    subroutine inspect(seed)
        character(*), optional, intent(in) :: seed
        typeof(seed) :: copy
    end subroutine
end program
