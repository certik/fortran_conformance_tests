program p
implicit none
type :: record
    integer :: count
    real :: number
    complex :: pair
    logical :: flag
    character(2) :: label
end type
type(record) :: value
value%count = 11
value%number = 0.0
value%pair = (0.0,0.0)
value%flag = .true.
value%label = 'AB'
if (value%count /= 11 .or. value%number /= 0.0) error stop 1
if (value%pair /= (0.0,0.0)) error stop 2
if (.not. value%flag .or. value%label /= 'AB') error stop 3
end program
