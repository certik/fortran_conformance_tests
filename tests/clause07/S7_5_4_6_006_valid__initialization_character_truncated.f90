! rule: S7.5.4.6-006
! covers: character-length-conversion
! evidence: effect
! standard: f2023
program component_witness
implicit none
type :: record
character(2) :: text='abcd'
end type
type(record) :: item
if (len(item%text) /= 2) error stop 1
if (item%text /= 'ab') error stop 2
end program
