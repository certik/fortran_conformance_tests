! rule: S7.5.4.6-008
! covers: explicit-array-object
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: inner
integer :: value=3
end type
type(inner) :: items(2)=[inner(2),inner(5)]
if (size(items) /= 2) error stop 1
if (any(items%value /= [2,5])) error stop 2
end program
