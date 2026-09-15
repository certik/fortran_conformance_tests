! rule: S7.5.2.3-001
! covers: numeric-storage-order
! evidence: effect
! standard: f2023
program p
implicit none
type :: record
    sequence
    integer :: first, second
end type
type(record) :: value
integer :: flat(2)
equivalence(value,flat)
value%first = 11
value%second = 13
if (flat(1) /= 11 .or. flat(2) /= 13) error stop 1
flat(2) = 17
if (value%first /= 11 .or. value%second /= 17) error stop 2
end program
