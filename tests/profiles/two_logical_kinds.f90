program two_logical_kinds
    use iso_fortran_env, only: logical_kinds
    implicit none
    if (count(logical_kinds /= kind(.true.)) == 0) stop 77
end program
