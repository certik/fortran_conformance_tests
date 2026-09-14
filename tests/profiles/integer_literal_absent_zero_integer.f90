program integer_literal_absent_zero
    use iso_fortran_env, only: integer_kinds
    implicit none
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (any(integer_kinds == 0)) stop 77
end program
