! rule: S7.5.3.2-001
! covers: definition-statement-order
! evidence: effect
! standard: f2023
program parameter_order
implicit none
type :: packet(left,right)
integer, kind :: right
integer, kind :: left
integer :: payload
end type
type(packet(2,3)) :: item
item%payload = 0
if (item%left /= 2 .or. item%right /= 3) error stop 1
end program
