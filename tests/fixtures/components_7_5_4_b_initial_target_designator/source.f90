module component_initial_target_designator_m
implicit none
type :: cell
  integer :: value
end type
type(cell), target, save :: cells(2) = [cell(11), cell(22)]
type :: holder
  integer, pointer :: alias => cells(2)%value
end type
end module
program component_initial_target_designator
use component_initial_target_designator_m
implicit none
type(holder) :: item
if (.not. associated(item%alias, cells(2)%value)) error stop 1
if (item%alias /= 22) error stop 2
item%alias = 29
if (cells(1)%value /= 11) error stop 3
if (cells(2)%value /= 29) error stop 4
print '(a)', 'COMPONENTS 7.5.4B DESIGNATOR OK'
end program
