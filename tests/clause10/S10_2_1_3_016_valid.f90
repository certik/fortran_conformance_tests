! rule: S10.2.1.3-016
! covers: integer-rhs real-rhs complex-kind-change both-components array-conversion
! F2023 10.2.1.3 p8, Table 10.9.
program s10_2_1_3_016_valid
    implicit none
    integer, parameter :: dp = kind(0.0d0)
    integer :: n
    real :: r
    complex :: normal
    complex(dp) :: wide, a(2)
    n = -17
    normal = (1.0, 99.0)
    normal = n
    if (real(normal) /= -17.0 .or. aimag(normal) /= 0.0) error stop 'integer-rhs'
    r = 2.5
    wide = (1.0_dp, 99.0_dp)
    wide = r
    if (real(wide) /= 2.5_dp .or. aimag(wide) /= 0.0_dp) error stop 'real-rhs'
    wide = (1.5_dp, -2.5_dp)
    normal = wide
    if (real(normal) /= 1.5 .or. aimag(normal) /= -2.5) error stop 'both-components'
    normal = (-3.5, 4.5)
    wide = normal
    if (real(wide) /= -3.5_dp .or. aimag(wide) /= 4.5_dp) error stop 'complex-kind-change'
    a = [(1.5, -2.5), (-3.5, 4.5)]
    if (real(a(1)) /= 1.5_dp .or. aimag(a(1)) /= -2.5_dp) error stop 'array-first'
    if (real(a(2)) /= -3.5_dp .or. aimag(a(2)) /= 4.5_dp) error stop 'array-second'
end program
