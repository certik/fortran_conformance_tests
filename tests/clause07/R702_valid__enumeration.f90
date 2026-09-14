! rule: R702
! covers: enumeration
! evidence: positive-control
! standard: f2023
program r702_enumeration
    implicit none
    enumeration type :: tone
        enumerator :: low, high
    end enumeration type
    type(tone) :: values(2)
    values = [tone :: low, high]
    if (size(values) /= 2) error stop 'size'
    if (values(1) /= low .or. values(2) /= high) error stop 'values'
end program
