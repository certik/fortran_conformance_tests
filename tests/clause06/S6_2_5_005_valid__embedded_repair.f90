! rule: S6.2.5-005
! covers: embedded-statement-exclusion
! evidence: positive-control
program label_embedded
    implicit none
    integer :: value
    value = 0
    if (.true.) value = 1
    if (value /= 1) error stop 1
end program
