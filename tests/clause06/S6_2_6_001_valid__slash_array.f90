! rule: S6.2.6-001
! covers: slash-array-open slash-array-close
! evidence: positive-control
program delimiter_slash_array_admission
    implicit none
    integer :: values(2)

    values = (/6, 10/)
    if (values(1) /= 6) error stop 1
    if (values(2) /= 10) error stop 2
end program delimiter_slash_array_admission
