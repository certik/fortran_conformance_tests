program p
implicit none
type :: record
    integer, allocatable, codimension[:,:] :: local[:], inherited
end type
type(record), save :: value
integer :: stat
if (num_images() /= 1) error stop 1
if (allocated(value%local)) error stop 2
allocate(value%local[0:*], stat=stat)
if (stat /= 0) error stop 3
if (.not. allocated(value%local)) error stop 4
if (allocated(value%inherited)) error stop 2
allocate(value%inherited[0:0,1:*], stat=stat)
if (stat /= 0) error stop 3
if (.not. allocated(value%inherited)) error stop 4
if (size(lcobound(value%local)) /= 1) error stop 21
if (size(lcobound(value%inherited)) /= 2) error stop 22
if (any(lcobound(value%local) /= [0])) error stop 23
if (any(lcobound(value%inherited) /= [0,1])) error stop 24
value%local = 11
value%inherited = 13
if (value%local /= 11 .or. value%inherited /= 13) error stop 25
deallocate(value%local, stat=stat)
if (stat /= 0) error stop 31
if (allocated(value%local)) error stop 32
deallocate(value%inherited, stat=stat)
if (stat /= 0) error stop 31
if (allocated(value%inherited)) error stop 32
end program
