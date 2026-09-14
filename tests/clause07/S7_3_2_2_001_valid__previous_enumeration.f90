! rule: S7.3.2.2-001
! covers: previous-enumeration
! evidence: positive-control
! standard: f2023
program type_previous_enumeration
    implicit none
    enumeration type :: choice
        enumerator :: low, high
    end enumeration type
    type(choice) :: value
    value = high
    if (int(value) /= 2) error stop 'enumeration-ordinal'
end program
