! rule: S7.5.4.6-007
! covers: multiple-nesting-levels
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: inner
integer :: value=3
end type
type :: middle
type(inner) :: nested=inner(7)
end type
type :: outer
type(middle) :: nested=middle(inner(11))
end type
type(outer) :: item
if (item%nested%nested%value /= 11) error stop 1
end program
