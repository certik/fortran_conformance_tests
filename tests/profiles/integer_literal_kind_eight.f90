program integer_literal_kind_eight
    use iso_fortran_env, only: integer_kinds
    implicit none
    integer, parameter :: probe = merge(8, kind(0), any(integer_kinds == 8))
    if (size(integer_kinds) < 1) error stop 1
    if (.not. any(integer_kinds == kind(0))) error stop 2
    if (.not. any(integer_kinds == 8)) stop 77
    if (huge(0_probe) < 47) stop 77
end program
