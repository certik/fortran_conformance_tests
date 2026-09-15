









subroutine c722_named_constant()
    implicit none
    integer, parameter :: k = kind(0.0)
    real :: r
    r = 1.0_k   ! {error C722 named-constant}
end subroutine
