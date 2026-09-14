! rule: S7.3.2.3-005
! covers: concrete-effective-argument polymorphic-effective-argument
! evidence: effect
program dynamic_effective_arguments
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    type(child) :: concrete
    class(root), allocatable :: polymorphic
    integer :: status = -1, seen = -1
    concrete%base = 11
    concrete%extra = 13
    call inspect(concrete, 11, seen)
    if (seen /= 13) error stop 'concrete-call'
    allocate(child :: polymorphic, stat=status)
    if (status /= 0) error stop 'actual-allocation'
    if (.not. allocated(polymorphic)) error stop 'actual-unallocated'
    select type (polymorphic)
    type is (child)
        polymorphic%base = 23
        polymorphic%extra = 13
    class default
        error stop 'actual-dynamic-type'
    end select
    seen = -1
    call inspect(polymorphic, 23, seen)
    if (seen /= 13) error stop 'polymorphic-call'
    deallocate(polymorphic)
contains
    subroutine inspect(x, expected, observed)
        class(root), intent(in) :: x
        integer, intent(in) :: expected
        integer, intent(out) :: observed
        observed = -1
        select type (x)
        type is (child)
            if (x%base /= expected) error stop 'dummy-base'
            observed = x%extra
        class default
            error stop 'dummy-dynamic-type'
        end select
    end subroutine
end program
