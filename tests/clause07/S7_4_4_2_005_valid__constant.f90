! rule: S7.4.4.2-005
! covers: constant-negative
! evidence: effect
! standard: f2023
program character_type_case
implicit none
character(-2) :: negative
character(0) :: empty
character(1) :: one
negative = ''
empty = ''
one = 'X'
if (len(negative) /= 0 .or. negative%len /= 0) error stop 1
if (len(empty) /= 0 .or. empty%len /= 0) error stop 2
if (len(one) /= 1 .or. one /= 'X') error stop 3
end program
