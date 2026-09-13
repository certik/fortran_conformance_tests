! rule: S10.2.1.3-001
! covers: enumeration-value
! standard: f2023
! F2023 10.2.1.3 p1: enumeration values, distinct from the enum conversion in -022.
program s10_2_1_3_001_enumeration
    implicit none
    enumeration type :: colour
        enumerator :: red, green, blue
    end enumeration type
    type(colour) :: source, copy, values(2)
    source = green
    copy = blue
    copy = source
    if (copy /= green) error stop 'enumeration-scalar'
    values = [red, blue]
    values = values(2:1:-1)
    if (values(1) /= blue .or. values(2) /= red) error stop 'enumeration-array'
end program
