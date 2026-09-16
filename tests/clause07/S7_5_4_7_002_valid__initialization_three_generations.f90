! rule: S7.5.4.7-002
! covers: multi-generation-order
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: parent
integer :: zed, alpha
end type
type, extends(parent) :: middle
integer :: extra
end type
type, extends(middle) :: child
integer :: last
end type
type(child) :: item
item=child(2,3,5,7)
if (item%zed /= 2 .or. item%alpha /= 3) error stop 1
if (item%extra /= 5 .or. item%last /= 7) error stop 2
end program
