! rule: R723
! covers: parenthesized-expression
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
character :: positive*(2+1), negative*(-2), empty*(0)
positive = 'ABC'
negative = ''
empty = ''
if (len(positive) /= 3) error stop 1
if (len(negative) /= 0 .or. len(empty) /= 0) error stop 2
if (positive /= 'ABC') error stop 3
end program
