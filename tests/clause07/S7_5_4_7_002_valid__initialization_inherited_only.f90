! rule: S7.5.4.7-002
! covers: no-new-components
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: parent
integer :: zed, alpha
end type
type, extends(parent) :: child
end type
type(child) :: item
item=child(2,3)
if (item%zed /= 2 .or. item%alpha /= 3) error stop 1
end program
