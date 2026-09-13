! rule: S10.2.1.3-022
! covers: enumerator-based-integer-expression constructor-control enum-array same-enum-control
! standard: f2023
! F2023 10.2.1.3 p13 and Table 10.8: integer RHS expressions contain an enum primary.
program s10_2_1_3_022_valid
    implicit none
    enum, bind(c) :: colour
        enumerator :: red = 2, green = 5, blue = 9
    end enum
    type(colour) :: value, values(2)
    value = red + 3
    if (value /= green) error stop 'enumerator-based-integer-expression'
    value = colour(9)
    if (value /= blue) error stop 'constructor-control'
    value = red
    if (value /= red) error stop 'same-enum-control'
    values = [red + 3, green + 4]
    if (values(1) /= green .or. values(2) /= blue) error stop 'enum-array'
end program
