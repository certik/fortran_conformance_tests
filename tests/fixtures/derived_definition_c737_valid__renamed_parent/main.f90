program p
use parent_module, only: local_parent => original
implicit none
type, extends(local_parent) :: child
end type
type(child) :: value
value%payload = 17
if (value%payload /= 17) error stop 1
end program
