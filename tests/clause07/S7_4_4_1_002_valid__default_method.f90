! rule: S7.4.4.1-002
! covers: required-default-method
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character :: bare
character(kind=kind('A')) :: explicit
bare = 'B'
explicit = 'C'
if (kind(bare) /= kind('A')) error stop 1
if (kind(explicit) /= kind(bare)) error stop 2
if (selected_char_kind('DEFAULT') /= kind('A')) error stop 3
if (bare /= 'B' .or. explicit /= 'C') error stop 4
end program
