! rule: R703
! covers: type-enum
! evidence: positive-control
! standard: f2023
program r703_type_enum
    implicit none
    enum, bind(c) :: tone
        enumerator :: low = 2, high = 5
    end enum
    type(tone) :: value
    value = tone(high)
    if (value /= tone(5)) error stop 'value'
end program
