! rule: R728
! covers: extends-attribute
! evidence: positive-control
! standard: f2023
program p
implicit none
type :: parent
    integer :: inherited
end type
type, extends(parent) :: child
    integer :: added
end type
type(child) :: value
value%inherited = 11
value%added = 13
if (value%inherited /= 11 .or. value%added /= 13) error stop 1
end program
