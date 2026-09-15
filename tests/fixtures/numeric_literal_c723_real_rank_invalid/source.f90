subroutine p
    implicit none
    integer, parameter :: kd = kind(0.0d0)
    complex(kd) :: z
    integer, parameter :: scalar = 0
    integer, parameter :: bad(1) = [0]
    data z /(bad, 0.0d0)/
end subroutine
