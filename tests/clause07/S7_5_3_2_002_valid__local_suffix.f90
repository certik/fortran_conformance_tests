! rule: S7.5.3.2-002
! covers: local-header-suffix
! evidence: effect
! standard: f2023
program inherited_order
implicit none
type :: parent(first,second)
integer, kind :: first
integer, len :: second
integer :: payload
end type
type, extends(parent) :: child(third,fourth)
integer, kind :: fourth,third
end type
type(child(2,3,5,7)) :: item
item%payload = 0
if (item%first /= 2 .or. item%second /= 3) error stop 1
if (item%third /= 5 .or. item%fourth /= 7) error stop 2
end program
