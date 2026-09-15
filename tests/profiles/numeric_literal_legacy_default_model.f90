program legacy_default_model
    use iso_fortran_env, only: real_kinds
    implicit none
    if (size(real_kinds) < 2) error stop 1
    if (.not. any(real_kinds == kind(0.0))) error stop 2
    if (.not. any(real_kinds == kind(0.0d0))) error stop 3
    if (precision(0.0d0) <= precision(0.0)) error stop 4
    if (precision(0.0d0) < 10 .or. range(0.0d0) < 37) error stop 5
    ! A numerical model bound, not a rounding or physical-format assertion.
    if (radix(0.0) /= 2) stop 77
    if (digits(0.0) < 3 .or. range(0.0) < 1) stop 77
    print *, 'default kind,radix,digits,range'
    print *, kind(0.0), radix(0.0), digits(0.0), range(0.0)
end program
