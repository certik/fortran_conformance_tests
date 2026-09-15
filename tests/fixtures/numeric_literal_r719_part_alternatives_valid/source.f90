subroutine p
    implicit none
    integer, parameter :: kd = kind(0.0d0)
    integer, parameter :: ni = -1
    real(kd), parameter :: nr = -0.0_kd
    complex(kd) :: a(2)
    data a(1) /(ni, 0.0d0)/
    data a(2) /(nr, 0.0d0)/
end subroutine
