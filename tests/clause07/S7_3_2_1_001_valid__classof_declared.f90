! rule: S7.3.2.1-001
! covers: classof-declared-polymorphic
! evidence: effect
! standard: f2023
program classof_declared
    implicit none
    type :: root
        integer :: code
    end type
    type, extends(root) :: first
        integer :: first_value
    end type
    type, extends(root) :: second
        integer :: second_value
    end type
    class(root), allocatable :: seed
    allocate(first :: seed)
    if (.not. allocated(seed)) error stop 'allocation'
    select type (seed)
    type is (first)
        seed%code = 3
        seed%first_value = 11
    class default
        error stop 'seed-type'
    end select
    call inspect(seed)
contains
    subroutine inspect(source)
        class(root), intent(in) :: source
        classof(source), allocatable :: copy
        select type (source)
        type is (first)
            if (source%code /= 3 .or. source%first_value /= 11) error stop 'seed-value'
        class default
            error stop 'entry-dynamic-type'
        end select
        allocate(second :: copy)
        if (.not. allocated(copy)) error stop 'sibling-allocation'
        select type (copy)
        type is (second)
            copy%code = 7
            copy%second_value = 13
            if (copy%code /= 7 .or. copy%second_value /= 13) error stop 'sibling-values'
        class default
            error stop 'sibling-type'
        end select
        deallocate(copy)
        allocate(root :: copy)
        if (.not. allocated(copy)) error stop 'root-allocation'
        copy%code = 17
        select type (copy)
        type is (root)
            if (copy%code /= 17) error stop 'root-value'
        class default
            error stop 'declared-root-type'
        end select
    end subroutine
end program
