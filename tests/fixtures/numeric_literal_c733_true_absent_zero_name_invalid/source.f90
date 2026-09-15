subroutine p
    implicit none
    integer, parameter :: lk = kind(.false.)
    integer, parameter :: bad = 0
    logical(lk) :: x
    data x /.true._bad/
end subroutine
