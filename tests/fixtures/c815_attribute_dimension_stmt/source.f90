








subroutine c815_dimension_stmt()
    implicit none
    integer, dimension(3) :: a
       ! {error C815 dimension-stmt}
    a = 1
end subroutine
















