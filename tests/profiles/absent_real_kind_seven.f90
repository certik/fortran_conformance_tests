program absent_real_kind_seven
    use iso_fortran_env, only: real_kinds
    implicit none
    if (any(real_kinds == 7)) stop 77
end program
