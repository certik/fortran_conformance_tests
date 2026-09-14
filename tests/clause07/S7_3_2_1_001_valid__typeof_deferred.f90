! rule: S7.3.2.1-001
! covers: typeof-deferred
! evidence: effect
! standard: f2023
program typeof_deferred
    implicit none
    character(:), allocatable :: seed
    allocate(character(3) :: seed)
    if (.not. allocated(seed)) error stop 'seed-allocation'
    seed(:) = 'abc'
    call inspect(seed)
contains
    subroutine inspect(source)
        character(:), allocatable, intent(in) :: source
        typeof(source), allocatable :: copy
        if (.not. allocated(source)) error stop 'source-allocation'
        if (len(source) /= 3) error stop 'source-length'
        allocate(character(5) :: copy)
        if (.not. allocated(copy)) error stop 'first-allocation'
        if (len(copy) /= 5) error stop 'first-length'
        copy(:) = 'hello'
        if (copy /= 'hello') error stop 'first-value'
        deallocate(copy)
        allocate(character(2) :: copy)
        if (.not. allocated(copy)) error stop 'second-allocation'
        if (len(copy) /= 2) error stop 'second-length'
        copy(:) = 'ok'
        if (copy /= 'ok') error stop 'second-value'
        if (len(source) /= 3 .or. source /= 'abc') error stop 'source-unchanged'
    end subroutine
end program
