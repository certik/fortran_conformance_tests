program p
implicit none
type :: record
    integer, allocatable, codimension[:,:] :: field(:)
end type
type(record), save :: value
integer :: stat
if (num_images() /= 1) error stop 1
if (allocated(value%field)) error stop 2
allocate(value%field(2)[0:0,1:*], stat=stat)
if (stat /= 0) error stop 3
if (.not. allocated(value%field)) error stop 4
value%field = [11,13]
if (rank(value%field) /= 1 .or. size(value%field) /= 2) error stop 21
if (size(lcobound(value%field)) /= 2) error stop 22
if (any(lcobound(value%field) /= [0,1])) error stop 23
if (any(value%field /= [11,13])) error stop 24
deallocate(value%field, stat=stat)
if (stat /= 0) error stop 31
if (allocated(value%field)) error stop 32
end program
