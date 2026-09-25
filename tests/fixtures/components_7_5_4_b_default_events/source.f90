module component_default_events_m
implicit none
type :: record
  integer :: value = 7
end type
contains
subroutine verify(item, code)
  type(record), intent(in) :: item
  integer, intent(in) :: code
  if (item%value /= 7) error stop code
end subroutine
subroutine reset(item)
  type(record), intent(out) :: item
  call verify(item, 30)
end subroutine
end module
program component_default_events
use component_default_events_m
implicit none
type(record) :: local
type(record), allocatable :: allocated
integer :: stat
call verify(local, 1)
allocate(allocated, stat=stat)
if (stat /= 0) error stop 2
call verify(allocated, 3)
allocated%value = 99
call reset(allocated)
call verify(allocated, 4)
print '(a)', 'COMPONENTS 7.5.4B DEFAULT EVENTS OK'
end program
