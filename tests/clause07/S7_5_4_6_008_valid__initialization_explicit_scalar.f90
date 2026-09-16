! rule: S7.5.4.6-008
! covers: explicit-scalar-object
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: inner
integer :: value=3
end type
type(inner) :: item=inner(7), defaults
if (item%value /= 7) error stop 1
if (defaults%value /= 3) error stop 2
end program
