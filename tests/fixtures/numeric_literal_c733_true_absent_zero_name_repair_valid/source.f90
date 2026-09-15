subroutine p
    implicit none
    integer, parameter :: lk = kind(.false.)
    integer, parameter :: bad = kind(.false.)
    logical(lk) :: x
    data x /.true._bad/
end subroutine
