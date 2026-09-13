! rule: S10.2.1.3-014
! covers: positive-fraction negative-fraction complex-rhs array-conversion
! F2023 10.2.1.3 p8, Table 10.9: independent integer oracles.
program s10_2_1_3_014_valid
    implicit none
    integer :: n, a(4)
    real :: value
    complex :: z
    value = 3.75
    n = value
    if (n /= 3) error stop 'positive-fraction'
    value = -3.75
    n = value
    if (n /= -3) error stop 'negative-fraction'
    z = (4.75, -99.0)
    n = z
    if (n /= 4) error stop 'complex-rhs'
    z = (-4.75, 99.0)
    n = z
    if (n /= -4) error stop 'negative-complex-rhs'
    a = [2.5, -2.5, 0.0, 7.5]
    if (any(a /= [2, -2, 0, 7])) error stop 'array-conversion'
end program
