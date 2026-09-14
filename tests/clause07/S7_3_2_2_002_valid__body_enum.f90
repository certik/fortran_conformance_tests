! rule: S7.3.2.2-002
! covers: body-local-enum-result
! evidence: effect
! standard: f2023
program type_body_enum
    implicit none
    if (int(make()) /= 7) error stop 'body-enum-value'
contains
    type(local_choice) function make() result(r)
        enum, bind(c) :: local_choice
            enumerator :: chosen = 7
        end enum
        r = local_choice(chosen)
    end function
end program
