! rule: C744
! covers: case-equivalent-name
! evidence: positive-control
! standard: f2023
program p
implicit none
type :: MiXeD
    integer :: payload
end type mixed
type(MIXED) :: value
value%payload = 11
if (value%payload /= 11) error stop 1
end program
