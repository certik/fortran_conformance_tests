! rule: R721
! covers: kind-len-keywords
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character(kind=kind('A'),len=2+1) :: text
text = 'ABC'
if (len(text) /= 3) error stop 1
if (kind(text) /= kind('A')) error stop 2
if (text /= 'ABC') error stop 3
end program
