subroutine p
    implicit none
    integer, parameter :: lk = kind(.false.)
    logical(lk) :: a(6)
    data a /.TRUE., .false., .TRUE._lk, .FALSE._lk, .TrUe._LK, .FaLsE._lK/
end subroutine
