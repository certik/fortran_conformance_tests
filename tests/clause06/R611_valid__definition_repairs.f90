! rule: R611
! covers: six-digit-definition zero-padded-overlength-definition
! evidence: positive-control
program label_definition_repairs
    implicit none
    integer :: value
    value = 0
10000 value = value + 1
00001 value = value + 1
    if (value /= 2) error stop 1
end program
