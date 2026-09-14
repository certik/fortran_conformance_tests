! rule: S7.3.2.2-001
! covers: previous-enum
! evidence: positive-control
! standard: f2023
program type_previous_enum
    implicit none
    enum, bind(c) :: choice
        enumerator :: low = 3, high = 8
    end enum
    type(choice) :: value
    value = choice(high)
    if (int(value) /= 8) error stop 'enum-value'
end program
