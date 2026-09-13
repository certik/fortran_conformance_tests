! rule: S10.2.1.3-017
! covers: hexadecimal real-destination destination-kind
! profile: ieee-binary
! standard: f2023
! F2023 10.2.1.3 p9. The profile is checked before compiling these bit patterns.
program s10_2_1_3_017_real
    implicit none
    real :: normal
    double precision :: wide
    normal = z'3F800000'
    if (normal /= 1.0) error stop 'binary32-one'
    normal = z'C0200000'
    if (normal /= -2.5) error stop 'binary32-negative'
    wide = z'3FF0000000000000'
    if (wide /= 1.0d0) error stop 'binary64-one'
    wide = z'C004000000000000'
    if (wide /= -2.5d0) error stop 'binary64-negative'
end program
