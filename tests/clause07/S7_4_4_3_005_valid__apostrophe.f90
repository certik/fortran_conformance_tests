! rule: S7.4.4.3-005
! covers: empty-apostrophe
! evidence: effect
! standard: f2023
program character_type_case
implicit none
integer, parameter :: dk = kind('A')
if (len('') /= 0 .or. len(dk_'') /= 0) error stop 1
if (kind('') /= dk .or. kind(dk_'') /= dk) error stop 2
if (len('' // 'ABC') /= 3) error stop 3
if (len('ABC' // '') /= 3) error stop 4
if ('' // 'ABC' /= 'ABC') error stop 5
if ('ABC' // '' /= 'ABC') error stop 6
end program
