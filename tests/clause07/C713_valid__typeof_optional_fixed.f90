! rule: C713
! covers: typeof-optional-fixed
! evidence: positive-control
! standard: f2023
program c713_typeof_optional_fixed
    implicit none
    call inspect('abc')
    call inspect()
contains
    subroutine inspect(seed)
        character(3), optional, intent(in) :: seed
        typeof(seed) :: copy
        copy = 'xyz'
        if (len(copy) /= 3 .or. copy /= 'xyz') error stop 'copy'
        if (present(seed)) then
            if (seed /= 'abc') error stop 'seed'
        end if
    end subroutine
end program
