subroutine p
    implicit none
    integer, parameter :: kd = kind(0.0d0)
    real(kd) :: a, b, c, d, e
    data a, b, c, d, e /0.0d0, +0.0d0, -0.0d0, +0.0_kd, -0.0_kd/
end subroutine
