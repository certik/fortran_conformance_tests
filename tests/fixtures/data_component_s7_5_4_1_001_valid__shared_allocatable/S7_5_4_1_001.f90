program p
implicit none
type :: record
    integer, allocatable :: first(:), second(:)
end type
type(record) :: value
integer :: stat
if (allocated(value%first) .or. allocated(value%second)) error stop 1
allocate(value%first(2), stat=stat)
if (stat /= 0) error stop 2
if (.not. allocated(value%first)) error stop 3
if (allocated(value%second)) error stop 4
value%first = [11,13]
if (any(value%first /= [11,13])) error stop 5
allocate(value%second(3), stat=stat)
if (stat /= 0) error stop 6
if (.not. allocated(value%second)) error stop 7
value%second = [17,19,23]
if (size(value%first) /= 2 .or. size(value%second) /= 3) error stop 8
if (any(value%second /= [17,19,23])) error stop 9
deallocate(value%first, value%second, stat=stat)
if (stat /= 0) error stop 10
end program
