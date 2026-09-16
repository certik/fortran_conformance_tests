! rule: S7.5.4.6-006
! covers: scalar-to-array-expansion
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: record
integer :: values(-1:1)=3
end type
type(record) :: item
if (size(item%values) /= 3) error stop 1
if (lbound(item%values,1) /= -1 .or. ubound(item%values,1) /= 1) error stop 2
if (any(item%values /= [3,3,3])) error stop 3
end program
