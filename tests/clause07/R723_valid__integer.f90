! rule: R723
! covers: bare-integer-literal
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character*3 :: selector
character :: individual*3
selector = 'ABC'
individual = 'xyz'
if (len(selector) /= 3 .or. len(individual) /= 3) error stop 1
if (selector /= 'ABC' .or. individual /= 'xyz') error stop 2
end program
