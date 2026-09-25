module component_target_compatibility_constraint_m
implicit none
integer, target, save :: target = 31
integer, target, save :: other = 31
type :: holder
  integer, pointer :: alias => target
end type
end module
program component_target_compatibility_constraint
use component_target_compatibility_constraint_m
implicit none
type(holder) :: item
if (.not. associated(item%alias, target)) error stop 1
if (item%alias /= 31) error stop 2
item%alias = 37
if (target /= 37) error stop 3
print '(a)', 'COMPONENTS 7.5.4B C769 LINK OK'
end program
