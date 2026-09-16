! rule: S7.5.4.6-006
! covers: character-length-conversion
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: record
character(5) :: text='ab'
end type
type(record) :: item
if (len(item%text) /= 5) error stop 1
if (item%text /= 'ab   ') error stop 2
end program
