! rule: S7.4.4.1-001
! covers: ordered-positions
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(4) :: text
text = 'aB3!'
if (len(text) /= 4) error stop 1
if (text(1:1) /= 'a') error stop 2
if (text(2:2) /= 'B') error stop 3
if (text(3:3) /= '3') error stop 4
if (text(4:4) /= '!') error stop 5
if (text(2:3) /= 'B3') error stop 6
if (text(1:1) == text(2:2)) error stop 7
end program
