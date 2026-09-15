! rule: R730
! covers: named-ending
! evidence: positive-control
! standard: f2023
program p
implicit none
type :: record
    integer :: payload
end type record
type(record) :: value
value%payload = 11
if (value%payload /= 11) error stop 1
end program
