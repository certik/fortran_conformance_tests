! rule: S10.2.1.3-017
! covers: binary octal hexadecimal integer-destination
! standard: f2023
! F2023 10.2.1.3 p9: direct BOZ assignment, not a call to a conversion intrinsic.
program s10_2_1_3_017_valid
    implicit none
    integer :: n
    n = b'101101'
    if (n /= 45) error stop 'binary'
    n = o'157'
    if (n /= 111) error stop 'octal'
    n = z'7B'
    if (n /= 123) error stop 'hexadecimal'
    n = z'FF'
    if (n /= 255) error stop 'leading-zero-extension'
end program
