program integer_literal_absent_zero
    use iso_fortran_env, only: real_kinds
    implicit none
    if (size(real_kinds) < 1) error stop 1
    if (.not. any(real_kinds == kind(0.0))) error stop 2
    if (any(real_kinds == 0)) stop 77
end program
