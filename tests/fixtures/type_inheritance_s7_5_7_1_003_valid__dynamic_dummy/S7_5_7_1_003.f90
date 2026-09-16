program p
implicit none
type :: root
    integer :: payload
end type
type, extends(root) :: child
    integer :: child_marker
end type
type, extends(child) :: grand
    integer :: grand_marker
end type
type(grand) :: value
type(child) :: mold
type(root) :: base
logical :: observed
value%payload = 17
value%child_marker = 41
value%grand_marker = 43
mold%payload = 19
mold%child_marker = 47
base%payload = 23
call inspect_dynamic(value, mold, observed)
if (.not. observed) error stop 1
if (extends_type_of(base, mold)) error stop 2
contains
subroutine inspect_dynamic(item, child_mold, result)
class(root), intent(in) :: item
type(child), intent(in) :: child_mold
logical, intent(out) :: result
if (item%payload /= 17 .or. child_mold%payload /= 19) error stop 3
result = extends_type_of(item, child_mold)
end subroutine
end program p
