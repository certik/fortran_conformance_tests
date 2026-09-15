! rule: S7.4.4.3-003
! covers: apostrophe-delimiter-exclusion
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: text = 'AbC'
if (len('') /= 0) error stop 1
if (len('X') /= 1) error stop 2
if (len('AbC') /= 3) error stop 3
if (text(1:1) /= 'A' .or. text(2:2) /= 'b' .or. text(3:3) /= 'C') error stop 4
end program
