module definitions
implicit none
type :: record(n,m)
    integer, len :: n,m
    character(n) :: label
    integer :: values(m)
    procedure(iface), pointer :: action
end type
abstract interface
    subroutine iface(self,tag)
        import :: record
        class(record(*,*)), intent(in) :: self
        integer, intent(out) :: tag
    end subroutine
end interface
contains
subroutine implementation(self,tag)
class(record(*,*)), intent(in) :: self
integer, intent(out) :: tag
if (self%n /= 2 .or. self%m /= 3) error stop 5
if (self%label /= 'AB') error stop 6
if (any(self%values /= [11,13,17])) error stop 7
tag = 19
end subroutine
end module
program p
use definitions
implicit none
type(record(2,3)) :: value
integer :: tag
value%label = 'AB'
value%values = [11,13,17]
nullify(value%action)
value%action => implementation
if (.not. associated(value%action)) error stop 1
call value%action(tag)
if (tag /= 19) error stop 2
end program
