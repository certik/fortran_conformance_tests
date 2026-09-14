! rule: R703
! covers: intrinsic
! evidence: positive-control
program r703_intrinsic
    implicit none
    integer(kind(0)) :: value
    value = 7
    if (value /= 7) error stop 'value'
end program
