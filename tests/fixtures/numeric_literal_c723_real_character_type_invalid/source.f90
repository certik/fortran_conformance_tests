subroutine p
    implicit none
    integer, parameter :: kd = kind(0.0d0)
    complex(kd) :: z
    integer, parameter :: scalar = 0
    character, parameter :: bad = 'a'
    data z /(bad, 0.0d0)/
end subroutine
