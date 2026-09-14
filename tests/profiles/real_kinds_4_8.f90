program real_kinds_4_8
    use iso_fortran_env, only: real_kinds
    implicit none
    if (.not. any(real_kinds == 4)) stop 77
    if (.not. any(real_kinds == 8)) stop 77
end program
