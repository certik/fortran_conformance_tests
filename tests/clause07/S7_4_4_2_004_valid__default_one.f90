! rule: S7.4.4.2-004
! covers: omitted-length-one
! evidence: effect
! standard: f2023
program character_type_case
implicit none
type :: record
    character :: text
end type
character :: bare, sibling*3
character(kind=kind('A')) :: kind_only
type(record) :: item
bare = 'A'
kind_only = 'B'
sibling = 'cde'
item%text = 'F'
if (len(bare) /= 1 .or. len(kind_only) /= 1 .or. len(item%text) /= 1) error stop 1
if (len(sibling) /= 3) error stop 2
if (bare /= 'A' .or. kind_only /= 'B' .or. item%text /= 'F') error stop 3
if (sibling /= 'cde') error stop 4
end program
