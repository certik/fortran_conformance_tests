module c715_class_receiver
    implicit none
contains
    subroutine probe(x)
        type(*), intent(in) :: x
        call sink(x)
    end subroutine
    subroutine sink(x)
        type(*), intent(in) :: x
    end subroutine
end module
