program p
implicit none
type :: record
    integer, allocatable :: field(:)
end type
type(record) :: value
integer :: stat
if (allocated(value%field)) error stop 1
allocate(value%field(2), stat=stat)
if (stat /= 0) error stop 2
if (.not. allocated(value%field)) error stop 3
value%field = [11,13]
if (size(value%field) /= 2) error stop 4
if (any(value%field /= [11,13])) error stop 5
deallocate(value%field, stat=stat)
if (stat /= 0) error stop 6
end program
