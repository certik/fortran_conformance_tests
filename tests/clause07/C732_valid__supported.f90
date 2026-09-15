! rule: C732
! covers: supported-prefix
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
integer, parameter :: dk = kind('A')
if (kind(dk_'ABC') /= dk .or. kind(dk_"xyz") /= dk) error stop 1
if (len(dk_'ABC') /= 3 .or. len(dk_"xyz") /= 3) error stop 2
if (dk_'ABC' /= 'ABC' .or. dk_"xyz" /= "xyz") error stop 3
end program
