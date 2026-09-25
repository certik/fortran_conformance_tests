program component_nested_override_events
implicit none
type :: inner
  integer :: value = 3
end type
type :: outer
  type(inner) :: nested = inner(11)
end type
type(outer) :: local
type(outer), allocatable :: allocated
integer :: stat
if (local%nested%value /= 11) error stop 1
allocate(allocated, stat=stat)
if (stat /= 0) error stop 2
if (allocated%nested%value /= 11) error stop 3
print '(a)', 'COMPONENTS 7.5.4B NESTED OVERRIDE OK'
end program
