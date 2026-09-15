! rule: S7.4.4.3-001
! covers: named-prefix-value
! evidence: effect
! standard: f2023
program character_type_case
implicit none
integer, parameter :: dk = kind('A')
integer, parameter :: selected_default = selected_char_kind('DEFAULT')
if (kind(dk_'ABC') /= dk .or. kind(dk_"xyz") /= dk) error stop 1
if (len(dk_'ABC') /= 3 .or. len(dk_"xyz") /= 3) error stop 2
if (kind(selected_default_'ABC') /= dk) error stop 3
if (kind(selected_default_"xyz") /= dk) error stop 4
if (len(selected_default_'ABC') /= 3) error stop 5
if (len(selected_default_"xyz") /= 3) error stop 6
if (dk_'ABC' /= selected_default_"ABC") error stop 7
if (dk_"xyz" /= selected_default_'xyz') error stop 8
end program
