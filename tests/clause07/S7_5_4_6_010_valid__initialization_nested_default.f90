! rule: S7.5.4.6-010
! covers: ordinary-nested-default
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: inner
integer :: value=3, untouched
end type
type :: outer
type(inner) :: nested
integer :: sibling
end type
type(outer) :: item
if (item%nested%value /= 3) error stop 1
item%nested%untouched=5
item%sibling=7
if (item%nested%untouched /= 5 .or. item%sibling /= 7) error stop 2
end program
