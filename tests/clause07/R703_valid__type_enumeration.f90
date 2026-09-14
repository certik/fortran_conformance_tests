! rule: R703
! covers: type-enumeration
! evidence: positive-control
! standard: f2023
program r703_type_enumeration
    implicit none
    enumeration type :: tone
        enumerator :: low, high
    end enumeration type
    type(tone) :: value
    value = high
    if (value /= high) error stop 'value'
end program
