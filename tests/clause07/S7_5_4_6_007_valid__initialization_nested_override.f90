! rule: S7.5.4.6-007
! covers: nested-value-override
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: inner
integer :: value=3
end type
type :: outer
type(inner) :: nested=inner(7)
end type
type(outer) :: item
if (item%nested%value /= 7) error stop 1
end program
