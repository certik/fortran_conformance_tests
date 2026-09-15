! rule: R721
! covers: kind-only
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character(kind=kind('A')) :: text
text = 'A'
if (len(text) /= 1) error stop 1
if (kind(text) /= kind('A')) error stop 2
if (text /= 'A') error stop 3
end program
