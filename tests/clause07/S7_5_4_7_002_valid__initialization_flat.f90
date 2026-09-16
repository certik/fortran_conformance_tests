! rule: S7.5.4.7-002
! covers: inherited-prefix-constructor
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: parent
integer :: zed, alpha
end type
type, extends(parent) :: child
integer :: middle
end type
type(child) :: item
item=child(2,3,5)
if (item%zed /= 2 .or. item%alpha /= 3 .or. item%middle /= 5) error stop 1
end program
