! rule: S7.5.3.2-002
! covers: inherited-only-extension
! evidence: effect
! standard: f2023
program inherited_order
implicit none
type :: parent(first,second)
integer, kind :: first
integer, len :: second
integer :: payload
end type
type, extends(parent) :: child
end type
type(child(2,3)) :: item
item%payload = 0
if (item%first /= 2 .or. item%second /= 3) error stop 1
end program
