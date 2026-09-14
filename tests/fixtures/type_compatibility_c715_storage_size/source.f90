subroutine probe(x)
    implicit none
    type(*), intent(in) :: x
    integer :: measured
    measured = storage_size(x)
end subroutine
