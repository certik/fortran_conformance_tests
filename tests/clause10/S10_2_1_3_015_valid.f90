! rule: S10.2.1.3-015
! covers: integer-rhs real-kind-change complex-rhs array-conversion
! F2023 10.2.1.3 p8, Table 10.9. Exact values avoid an assumed rounding mode.
program s10_2_1_3_015_valid
    implicit none
    integer, parameter :: dp = kind(0.0d0)
    integer :: n
    real :: normal, a(3)
    real(dp) :: wide
    complex(dp) :: z
    n = -17
    normal = n
    if (normal /= -17.0) error stop 'integer-rhs'
    wide = 1.5_dp
    normal = wide
    if (normal /= 1.5) error stop 'wide-to-default'
    normal = -2.5
    wide = normal
    if (wide /= -2.5_dp) error stop 'default-to-wide'
    z = (6.5_dp, -99.0_dp)
    normal = z
    if (normal /= 6.5) error stop 'complex-rhs'
    a = [2, -5, 9]
    if (any(a /= [2.0, -5.0, 9.0])) error stop 'array-conversion'
end program
