subroutine p
    implicit none
    integer, parameter :: lk = kind(.false.)
    logical(lk) :: a, b
    data a, b /.true._lk, .false._lk/
end subroutine
