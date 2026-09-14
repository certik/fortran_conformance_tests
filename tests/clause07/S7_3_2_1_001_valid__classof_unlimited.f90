! rule: S7.3.2.1-001
! covers: classof-unlimited
! evidence: effect
! standard: f2023
program classof_unlimited
    implicit none
    class(*), allocatable :: seed
    allocate(integer :: seed)
    if (.not. allocated(seed)) error stop 'seed-allocation'
    select type (seed)
    type is (integer)
        seed = 37
    class default
        error stop 'seed-type'
    end select
    call inspect(seed)
contains
    subroutine inspect(source)
        class(*), intent(in) :: source
        classof(source), allocatable :: copy
        select type (source)
        type is (integer)
            if (source /= 37) error stop 'source-value'
        class default
            error stop 'source-type'
        end select
        allocate(character(3) :: copy)
        if (.not. allocated(copy)) error stop 'character-allocation'
        select type (copy)
        type is (character(*))
            if (len(copy) /= 3) error stop 'character-length'
            copy = 'abc'
            if (copy /= 'abc') error stop 'character-value'
        class default
            error stop 'unlimited-character'
        end select
        deallocate(copy)
        allocate(real :: copy)
        if (.not. allocated(copy)) error stop 'real-allocation'
        select type (copy)
        type is (real)
            copy = 2.0
            if (copy /= 2.0) error stop 'real-value'
        class default
            error stop 'unlimited-real'
        end select
    end subroutine
end program
