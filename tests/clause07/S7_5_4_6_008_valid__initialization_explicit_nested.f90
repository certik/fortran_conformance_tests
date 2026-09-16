! rule: S7.5.4.6-008
! covers: explicit-nested-object
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
type(outer) :: item=outer(inner(11)), defaults
if (item%nested%value /= 11) error stop 1
if (defaults%nested%value /= 7) error stop 2
end program
