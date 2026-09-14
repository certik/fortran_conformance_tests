subroutine probe(x)
    implicit none
    type(*), intent(in) :: x
    integer :: measured
    measured = rank(x)
end subroutine
