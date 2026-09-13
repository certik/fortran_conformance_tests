! rule: S10.2.1.3-015
! covers: destination-precision
! profile: ieee-binary integer-range-nine
! F2023 10.2.1.3 p8: these integers are exact in binary64 but not binary32.
! Subtracting the exactly representable power of two avoids a rounding-mode assumption.
program s10_2_1_3_015_precision
    implicit none
    integer, parameter :: ik = selected_int_kind(9), dp = kind(0.0d0)
    integer(ik) :: value
    real(dp) :: converted
    value = 16777217_ik
    converted = value
    if (converted - 16777216.0_dp /= 1.0_dp) error stop 'positive-destination-precision'
    value = -16777217_ik
    converted = value
    if (converted + 16777216.0_dp /= -1.0_dp) error stop 'negative-destination-precision'
end program
