! rule: R722
! covers: integer-expression-kind
! evidence: positive-control
! standard: f2023
program character_type_case
implicit none
integer, parameter :: lk = selected_int_kind(4)
character(len=3_lk) :: selector
character :: individual*(3_lk)
selector = 'ABC'
individual = 'xyz'
if (len(selector) /= 3 .or. len(individual) /= 3) error stop 1
if (selector /= 'ABC' .or. individual /= 'xyz') error stop 2
end program
