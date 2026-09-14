! rule: S6.2.5-005
! covers: embedded-statement-exclusion
! case: labeled-action
program label_embedded
    implicit none
    integer :: value
    value = 0
    if (.true.) 10 value = 1 ! {error S6.2.5-005 labeled-action}
    if (value /= 1) error stop 1
end program
