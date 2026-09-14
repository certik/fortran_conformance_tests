program integer_literal_absent_zero
    use iso_fortran_env, only: logical_kinds
    implicit none
    if (size(logical_kinds) < 1) error stop 1
    if (.not. any(logical_kinds == kind(.true.))) error stop 2
    if (any(logical_kinds == 0)) stop 77
end program
