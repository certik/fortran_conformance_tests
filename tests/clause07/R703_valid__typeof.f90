! rule: R703
! covers: typeof
! evidence: positive-control
! standard: f2023
program r703_typeof
    implicit none
    real(kind(0.0d0)) :: seed = 1.0d0
    typeof(seed) :: value
    value = 2.0d0
    if (kind(value) /= kind(0.0d0)) error stop 'kind'
    if (value /= 2.0d0) error stop 'value'
end program
