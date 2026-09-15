subroutine p
    implicit none
    integer, parameter :: kd = kind(0.0d0)
    real :: a, b, c
    real(kd) :: d, e, f, g, h
    data a, b, c /0.0, 0.0e0, 0e0/
    data d, e, f, g, h /0.0d0, 0d0, 0.0_kd, 0.0e0_kd, 0e0_kd/
end subroutine
