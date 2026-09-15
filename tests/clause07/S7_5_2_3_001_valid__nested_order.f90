! rule: S7.5.2.3-001
! covers: nested-numeric-storage-order
! evidence: effect
! standard: f2023
program p
implicit none
type :: leaf
    sequence
    integer :: first, second
end type
type :: record
    sequence
    type(leaf) :: inner
    integer :: last
end type
type(record) :: value
integer :: flat(3)
equivalence(value,flat)
value%inner%first = 11
value%inner%second = 13
value%last = 17
if (any(flat /= [11,13,17])) error stop 1
flat(2) = 19
if (value%inner%first /= 11) error stop 2
if (value%inner%second /= 19 .or. value%last /= 17) error stop 3
end program
