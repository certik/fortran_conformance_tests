! rule: S7.3.2.2-002
! covers: body-local-enumeration-result
! evidence: effect
! standard: f2023
program type_body_enumeration
    implicit none
    if (int(make()) /= 2) error stop 'body-enumeration-ordinal'
contains
    type(local_choice) function make() result(r)
        enumeration type :: local_choice
            enumerator :: low, high
        end enumeration type
        r = high
    end function
end program
