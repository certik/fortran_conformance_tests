! rule: S7.4.4.2-004
! covers: component-override
! evidence: effect
! standard: f2023
program character_type_case
implicit none
type :: record
    character(len=5) :: short*2, empty*0, inherited
end type
type(record) :: item
item%short = 'AB'
item%empty = ''
item%inherited = 'cdefg'
if (len(item%short) /= 2 .or. len(item%empty) /= 0) error stop 1
if (len(item%inherited) /= 5) error stop 2
if (item%short /= 'AB' .or. item%inherited /= 'cdefg') error stop 3
end program
