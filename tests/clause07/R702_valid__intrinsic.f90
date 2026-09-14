! rule: R702
! covers: intrinsic
! evidence: positive-control
program r702_intrinsic
    implicit none
    integer(kind(0)) :: values(2)
    values = [integer(kind(0)) :: 2, 5]
    if (size(values) /= 2) error stop 'size'
    if (values(1) /= 2 .or. values(2) /= 5) error stop 'values'
end program
