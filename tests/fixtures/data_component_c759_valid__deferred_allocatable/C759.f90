program p
implicit none
type :: record
    character(:), allocatable :: field
end type
type(record) :: value
integer :: stat
if (allocated(value%field)) error stop 1
allocate(character(2) :: value%field, stat=stat)
if (stat /= 0) error stop 2
if (.not. allocated(value%field)) error stop 3
value%field = 'AB'
if (len(value%field) /= 2 .or. value%field /= 'AB') error stop 4
deallocate(value%field, stat=stat)
if (stat /= 0) error stop 5
end program
