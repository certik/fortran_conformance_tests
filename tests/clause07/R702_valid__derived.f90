! rule: R702
! covers: derived
! evidence: positive-control
program r702_derived
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: values(2)
    values = [payload :: payload(2), payload(5)]
    if (size(values) /= 2) error stop 'size'
    if (values(1)%code /= 2 .or. values(2)%code /= 5) error stop 'values'
end program
