! rule: C713
! covers: classof-optional-fixed
! evidence: positive-control
! standard: f2023
program c713_classof_optional_fixed
    implicit none
    type :: packet(n)
        integer, len :: n
        character(n) :: text
    end type
    type(packet(3)) :: value
    value%text = 'abc'
    call inspect(value)
    call inspect()
contains
    subroutine inspect(seed)
        class(packet(n=3)), optional, intent(in) :: seed
        classof(seed), allocatable :: copy
        allocate(packet(3) :: copy)
        if (.not. allocated(copy)) error stop 'allocation'
        copy%text = 'xyz'
        if (copy%n /= 3 .or. len(copy%text) /= 3) error stop 'length'
        if (copy%text /= 'xyz') error stop 'copy'
        if (present(seed)) then
            if (seed%text /= 'abc') error stop 'seed'
        end if
    end subroutine
end program
