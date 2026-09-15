! rule: S7.4.4.1-003
! covers: constructed-character-members
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character :: member
character(3) :: text
member = char(0, kind=kind('A'))
text = 'A' // member // 'Z'
if (len(member) /= 1 .or. len(text) /= 3) error stop 1
if (text(1:1) /= 'A' .or. text(3:3) /= 'Z') error stop 2
if (text(2:2) /= member) error stop 3
end program
