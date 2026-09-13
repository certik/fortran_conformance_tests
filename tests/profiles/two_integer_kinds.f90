program two_integer_kinds
    use iso_fortran_env, only: integer_kinds
    implicit none
    if (count(integer_kinds /= kind(0)) == 0) stop 77
end program
