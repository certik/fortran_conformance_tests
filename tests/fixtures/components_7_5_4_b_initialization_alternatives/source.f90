module component_initialization_alternatives_m
implicit none
integer, target, save :: target = 17
integer, target, save :: other = 23
type :: record
  integer :: value = 7
  integer, pointer :: empty => null()
  integer, pointer :: alias => target
end type
contains
subroutine reset(item)
  type(record), intent(out) :: item
  if (item%value /= 7) error stop 4
  if (associated(item%empty)) error stop 5
  if (.not. associated(item%alias, target)) error stop 6
end subroutine
end module
program component_initialization_alternatives
use component_initialization_alternatives_m
implicit none
type(record) :: local
type(record), allocatable :: allocated
integer :: stat
if (local%value /= 7) error stop 1
if (associated(local%empty)) error stop 2
if (.not. associated(local%alias, target)) error stop 3
allocate(allocated, stat=stat)
if (stat /= 0) error stop 7
if (allocated%value /= 7) error stop 8
if (associated(allocated%empty)) error stop 9
if (.not. associated(allocated%alias, target)) error stop 10
allocated%value = 99
allocated%empty => other
allocated%alias => other
call reset(allocated)
print '(a)', 'COMPONENTS 7.5.4B INITIALIZERS OK'
end program
