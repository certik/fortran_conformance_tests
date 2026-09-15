! rule: S7.4.4.2-004
! covers: entity-override
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(len=5,kind=kind('A')) :: short*2, empty*0, inherited
character :: standalone*3
short = 'AB'
empty = ''
inherited = 'cdefg'
standalone = 'XYZ'
if (len(short) /= 2 .or. len(empty) /= 0 .or. len(inherited) /= 5) error stop 1
if (len(standalone) /= 3) error stop 2
if (kind(short) /= kind('A') .or. kind(empty) /= kind('A')) error stop 3
if (kind(inherited) /= kind('A') .or. kind(standalone) /= kind('A')) error stop 4
if (short /= 'AB' .or. inherited /= 'cdefg' .or. standalone /= 'XYZ') error stop 5
end program
