! rule: R722
! covers: star-forms
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character*3 :: bare
character*(2+1) :: expression
bare = 'ABC'
expression = 'xyz'
if (len(bare) /= 3 .or. len(expression) /= 3) error stop 1
if (bare /= 'ABC' .or. expression /= 'xyz') error stop 2
end program
