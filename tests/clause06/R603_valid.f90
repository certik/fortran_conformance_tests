! rule: R603
! covers: single-letter letter-suffix digit-suffix
! evidence: positive-control
! Free-form source; no optional processor features.
program names_letters_digits
    implicit none
    integer :: A, z
    integer :: aABCDEFGHIJKLMNOPQRSTUVWXYZ, Zabcdefghijklmnopqrstuvwxyz
    integer :: n0123456789

    A = 3
    z = 5
    aABCDEFGHIJKLMNOPQRSTUVWXYZ = 8
    Zabcdefghijklmnopqrstuvwxyz = 13
    n0123456789 = 21

    if (A /= 3) error stop 1
    if (z /= 5) error stop 2
    if (aABCDEFGHIJKLMNOPQRSTUVWXYZ /= 8) error stop 3
    if (Zabcdefghijklmnopqrstuvwxyz /= 13) error stop 4
    if (n0123456789 /= 21) error stop 5
end program names_letters_digits
