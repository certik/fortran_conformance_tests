module component_nested_initial_target_m
implicit none
type :: cell
  integer :: value
end type
type :: box
  type(cell) :: payload(3)
end type
type(box), target, save :: saved = box([cell(3), cell(5), cell(7)])
type :: holder
  integer, pointer :: alias => saved%payload(2)%value
end type
end module
program component_nested_initial_target
use component_nested_initial_target_m
implicit none
type(holder) :: item
if (.not. associated(item%alias, saved%payload(2)%value)) error stop 1
if (item%alias /= 5) error stop 2
item%alias = 41
if (saved%payload(1)%value /= 3) error stop 3
if (saved%payload(2)%value /= 41) error stop 4
if (saved%payload(3)%value /= 7) error stop 5
print '(a)', 'COMPONENTS 7.5.4B NESTED TARGET OK'
end program
