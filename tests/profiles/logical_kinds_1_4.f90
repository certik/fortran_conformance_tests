program logical_kinds_1_4
    use iso_fortran_env, only: logical_kinds
    implicit none
    if (.not. any(logical_kinds == 1)) stop 77
    if (.not. any(logical_kinds == 4)) stop 77
end program
