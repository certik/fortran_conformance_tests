! rule: S7.3.2.1-001
! covers: classof-deferred
! evidence: effect
! standard: f2023
program classof_deferred
    implicit none
    type :: packet(n)
        integer, len :: n
        character(n) :: text
    end type
    class(packet(:)), allocatable :: seed
    allocate(packet(3) :: seed)
    if (.not. allocated(seed)) error stop 'seed-allocation'
    seed%text = 'abc'
    call inspect(seed)
contains
    subroutine inspect(source)
        class(packet(:)), allocatable, intent(in) :: source
        classof(source), allocatable :: copy
        if (.not. allocated(source)) error stop 'source-allocation'
        if (source%n /= 3 .or. len(source%text) /= 3) error stop 'source-length'
        allocate(packet(5) :: copy)
        if (.not. allocated(copy)) error stop 'first-allocation'
        if (copy%n /= 5 .or. len(copy%text) /= 5) error stop 'first-length'
        copy%text = 'hello'
        if (copy%text /= 'hello') error stop 'first-value'
        deallocate(copy)
        allocate(packet(2) :: copy)
        if (.not. allocated(copy)) error stop 'second-allocation'
        if (copy%n /= 2 .or. len(copy%text) /= 2) error stop 'second-length'
        copy%text = 'ok'
        if (copy%text /= 'ok') error stop 'second-value'
        if (source%n /= 3 .or. source%text /= 'abc') error stop 'source-unchanged'
    end subroutine
end program
