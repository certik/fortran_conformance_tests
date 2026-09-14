! rule: S6.2.6-001
! covers: left-square-bracket right-square-bracket
! evidence: positive-control
program delimiter_square_array_admission
    implicit none
    integer :: values(2)

    values = [5, 9]
    if (values(1) /= 5) error stop 1
    if (values(2) /= 9) error stop 2
end program delimiter_square_array_admission
