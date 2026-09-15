! rule: R722
! covers: optional-comma
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character*3, bare
character*(3), parenthesized
bare = 'ABC'
parenthesized = 'xyz'
if (len(bare) /= 3 .or. len(parenthesized) /= 3) error stop 1
if (bare /= 'ABC' .or. parenthesized /= 'xyz') error stop 2
end program
