! rule: R703
! covers: type-intrinsic
! evidence: positive-control
program r703_type_intrinsic
    implicit none
    type(integer(kind(0))) :: value
    value = 7
    if (value /= 7) error stop 'value'
end program
