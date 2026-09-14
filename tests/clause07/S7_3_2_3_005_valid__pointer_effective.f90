! rule: S7.3.2.3-005
! covers: pointer-target-effective-argument
! evidence: effect
program dynamic_pointer_effective
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    type(child), target :: target
    class(root), pointer :: actual => null()
    integer :: seen = -1
    target%base = 41
    target%extra = 7
    actual => target
    if (.not. associated(actual)) error stop 'actual-association'
    call inspect(actual, seen)
    if (seen /= 48) error stop 'effective-target-value'
    nullify(actual)
contains
    subroutine inspect(x, observed)
        class(root), intent(in) :: x
        integer, intent(out) :: observed
        observed = -1
        select type (x)
        type is (child)
            observed = x%base + x%extra
        class default
            error stop 'effective-target-type'
        end select
    end subroutine
end program
