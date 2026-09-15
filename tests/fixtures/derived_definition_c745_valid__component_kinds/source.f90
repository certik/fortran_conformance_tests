module definitions
implicit none
abstract interface
    integer function answer_interface()
    end function
end interface
type :: record
    sequence
    integer, pointer :: pointer_data(:)
    integer, allocatable :: allocated_data(:)
    procedure(answer_interface), pointer, nopass :: answer
end type
contains
integer function answer_implementation()
    answer_implementation = 17
end function
end module
program p
use definitions
implicit none
type(record) :: value
integer, target :: target(2)
integer :: stat
target = [11,13]
value%pointer_data => target
value%answer => answer_implementation
allocate(value%allocated_data(2), stat=stat)
if (stat /= 0) error stop 1
if (.not. allocated(value%allocated_data)) error stop 2
if (.not. associated(value%pointer_data)) error stop 3
if (.not. associated(value%answer)) error stop 4
value%allocated_data = [19,23]
if (any(value%pointer_data /= [11,13])) error stop 5
if (any(value%allocated_data /= [19,23])) error stop 6
if (value%answer() /= 17) error stop 7
end program
