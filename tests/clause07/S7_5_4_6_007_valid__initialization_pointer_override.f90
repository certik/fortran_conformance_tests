! rule: S7.5.4.6-007
! covers: nested-pointer-status-override
! evidence: effect
! standard: f2023
program component_witness
implicit none
integer, target, save :: target=11
type :: inner
integer :: value=3
integer, pointer :: alias => target
end type
type :: outer
type(inner) :: nested=inner(7,null())
end type
type(outer) :: item
if (item%nested%value /= 7) error stop 1
if (associated(item%nested%alias)) error stop 2
if (target /= 11) error stop 3
end program
