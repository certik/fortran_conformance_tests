! rule: C725
! covers: parenthesized-suffix-admission
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
integer, parameter :: ik = kind(0)
character*(3_ik) :: selector
character :: individual*(3_ik)
selector = 'ABC'
individual = 'xyz'
if (len(selector) /= 3 .or. len(individual) /= 3) error stop 1
if (selector /= 'ABC' .or. individual /= 'xyz') error stop 2
end program
