! rule: S7.2-001
! covers: literal-kind operation-kind
! evidence: effect
program type_parameters_real_effects
    implicit none
    integer, parameter :: rk = kind(0.0), dk = kind(0.0d0)
    real(kind=rk) :: ordinary = 0.0_rk
    real(kind=dk) :: wider = 0.0_dk

    if (rk == dk) error stop 1
    if (precision(wider) <= precision(ordinary)) error stop 2
    if (kind(0.0_rk) /= rk) error stop 3
    if (kind(0.0_dk) /= dk) error stop 4
    if (kind(ordinary + wider) /= dk) error stop 5
    if (ordinary + wider /= 0.0_dk) error stop 6
end program type_parameters_real_effects
