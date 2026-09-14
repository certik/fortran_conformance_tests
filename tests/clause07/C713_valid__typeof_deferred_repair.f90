! rule: C713
! covers: nonoptional-deferred
! evidence: positive-control
! standard: f2023
program c713_typeof_deferred
    implicit none
contains
    subroutine inspect(seed)
        character(:), allocatable, intent(in) :: seed
        typeof(seed), allocatable :: copy
    end subroutine
end program
