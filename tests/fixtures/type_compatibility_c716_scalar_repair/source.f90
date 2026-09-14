module c716_scalar
    implicit none
contains
    subroutine forward(x)
        type(*), intent(in) :: x(..)
        call sink(x)
    end subroutine
    subroutine sink(x)
        type(*), intent(in) :: x(..)
    end subroutine
end module
