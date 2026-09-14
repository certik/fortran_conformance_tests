! rule: S7.3.2.1-001
! covers: typeof-declared-nonpolymorphic
! evidence: effect
! standard: f2023
program typeof_declared
    implicit none
    type :: root
        integer :: code
    end type
    type, extends(root) :: leaf
        integer :: extra
    end type
    class(root), allocatable :: seed
    allocate(leaf :: seed)
    if (.not. allocated(seed)) error stop 'allocation'
    select type (seed)
    type is (leaf)
        seed%code = 3
        seed%extra = 11
    class default
        error stop 'seed-type'
    end select
    call inspect(seed)
contains
    subroutine inspect(source)
        class(root), intent(in) :: source
        typeof(source) :: copy
        select type (source)
        type is (leaf)
            if (source%code /= 3 .or. source%extra /= 11) error stop 'seed-value'
        class default
            error stop 'entry-dynamic-type'
        end select
        copy%code = 7
        call verify_root(copy)
    end subroutine
    subroutine verify_root(value)
        class(root), intent(in) :: value
        select type (value)
        type is (root)
            if (value%code /= 7) error stop 'copy-value'
        class default
            error stop 'copied-dynamic-instead-of-declared-type'
        end select
    end subroutine
end program
