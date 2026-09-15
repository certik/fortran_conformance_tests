! rule: S7.5.3.2-001
! covers: header-position-values
! evidence: effect
! standard: f2023
program parameter_order
implicit none
type :: packet(left,right)
integer, kind :: left
integer, kind :: right
integer :: payload
end type
type(packet(2,3)) :: item
item%payload = 0
if (item%left /= 2 .or. item%right /= 3) error stop 1
end program
