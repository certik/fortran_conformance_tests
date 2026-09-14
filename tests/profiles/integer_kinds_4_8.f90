program integer_kinds_4_8
    use iso_fortran_env, only: integer_kinds
    implicit none
    if (.not. any(integer_kinds == 4)) stop 77
    if (.not. any(integer_kinds == 8)) stop 77
end program
