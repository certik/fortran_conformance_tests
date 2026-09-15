! rule: C745
! covers: intrinsic-and-sequence-data
! evidence: positive-control
! standard: f2023
program p
implicit none
type :: leaf
    sequence
    integer :: payload
end type
type :: record
    sequence
    integer :: i
    real :: r
    double precision :: d
    complex :: z
    logical :: flag
    character(2) :: label
    type(leaf) :: nested
end type
type(record) :: value
value%i = 11
value%r = 0.0
value%d = 0.0d0
value%z = (0.0,0.0)
value%flag = .true.
value%label = 'AB'
value%nested%payload = 13
if (value%i /= 11 .or. value%nested%payload /= 13) error stop 1
if (value%r /= 0.0 .or. value%d /= 0.0d0) error stop 2
if (value%z /= (0.0,0.0)) error stop 3
if (.not. value%flag .or. value%label /= 'AB') error stop 4
end program
