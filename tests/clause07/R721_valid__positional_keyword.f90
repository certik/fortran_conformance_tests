! rule: R721
! covers: positional-len-keyword-kind
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character(2+1,kind=kind('A')) :: text
text = 'ABC'
if (len(text) /= 3) error stop 1
if (kind(text) /= kind('A')) error stop 2
if (text /= 'ABC') error stop 3
end program
