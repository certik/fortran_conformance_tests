! rule: C713
! covers: nonoptional-assumed
! evidence: positive-control
! standard: f2023
program c713_typeof_assumed
    implicit none
contains
    subroutine inspect(seed)
        character(*), intent(in) :: seed
        typeof(seed) :: copy
    end subroutine
end program
