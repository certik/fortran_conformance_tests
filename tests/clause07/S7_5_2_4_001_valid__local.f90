! rule: S7.5.2.4-001
! covers: local-definition
! evidence: effect
! standard: f2023
program p
implicit none
type :: record
    integer :: payload
end type
type(record) :: first, second
first%payload = 11
second%payload = 13
if (.not. same_type_as(first,second)) error stop 1
second = first
if (second%payload /= 11) error stop 2
end program
