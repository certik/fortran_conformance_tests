! rule: R727
! covers: bare-header
! evidence: positive-control
! standard: f2023
program p
implicit none
type record
    integer :: payload
end type
type(record) :: value
value%payload = 11
if (value%payload /= 11) error stop 1
end program
