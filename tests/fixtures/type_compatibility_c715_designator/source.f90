module c715_designator
    implicit none
contains
    subroutine probe(x)
        type(*), intent(in) :: x(:)
        call sink(x(1))
    end subroutine
    subroutine sink(x)
        type(*), intent(in) :: x
    end subroutine
end module
