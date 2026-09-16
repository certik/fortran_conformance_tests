module specifier_definitions
implicit none
type :: record(k,n)
integer, kind :: k
integer, len :: n
integer :: payload
end type record
contains
subroutine allocate_dummy(item)
type(record(k=7,n=*)), allocatable, intent(inout) :: item
integer :: status
if (.not.allocated(item)) then
allocate(record(k=7,n=*) :: item,stat=status)
if (status/=0) error stop 1
end if
item%payload=0
end subroutine allocate_dummy
subroutine possible_caller()
type(record(k=7,n=5)), allocatable :: actual
call allocate_dummy(actual)
end subroutine possible_caller
end module specifier_definitions
