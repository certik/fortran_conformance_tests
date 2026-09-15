subroutine p
    implicit none
    integer, parameter :: kd = kind(0.0d0)
    integer, parameter :: ik = selected_int_kind(18)
    complex(kd) :: a(4)
    data a(1) /(0, 0.0d0)/
    data a(2) /(+0, 0.0d0)/
    data a(3) /(-0, 0.0d0)/
    data a(4) /(0_ik, 0.0d0)/
end subroutine
