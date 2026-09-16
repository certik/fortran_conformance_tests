! rule: S7.5.4.7-001
! covers: positional-constructor-order same-statement-declaration-list
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: record
integer :: zed, alpha
integer :: middle
end type
type(record) :: item
item=record(2,3,5)
if (item%zed /= 2 .or. item%alpha /= 3 .or. item%middle /= 5) error stop 1
end program
