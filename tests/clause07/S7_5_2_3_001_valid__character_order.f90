! rule: S7.5.2.3-001
! covers: character-storage-order
! evidence: effect
! standard: f2023
program p
implicit none
type :: record
sequence
character(1) :: first
character(2) :: last
end type
type(record) :: value
character(3) :: flat
equivalence(value,flat)
value%first = 'A'
value%last = 'BC'
if (flat /= 'ABC') error stop 1
if (len(flat) /= 3) error stop 2
flat(1:1) = 'D'
flat(2:3) = 'EF'
if (value%first /= 'D' .or. value%last /= 'EF') error stop 3
end program
