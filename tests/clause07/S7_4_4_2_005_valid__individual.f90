! rule: S7.4.4.2-005
! covers: individual-negative
! evidence: effect
! standard: f2023
program character_type_case
implicit none
type :: record
    character(len=-2) :: empty
    character(len=3) :: normal
end type
character(len=5) :: overridden*(-2), sibling
type(record) :: item
overridden = ''
sibling = 'ABCDE'
item%empty = ''
item%normal = 'xyz'
if (len(overridden) /= 0 .or. len(sibling) /= 5) error stop 1
if (len(item%empty) /= 0 .or. len(item%normal) /= 3) error stop 2
if (sibling /= 'ABCDE' .or. item%normal /= 'xyz') error stop 3
end program
