! rule: S7.4.4.3-004
! covers: apostrophe-doubling-and-count
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(*), parameter :: text = 'A''B'
if (len(text) /= 3) error stop 1
if (text(1:1) /= 'A' .or. text(3:3) /= 'B') error stop 2
if (text(2:2) /= "'") error stop 3
end program
