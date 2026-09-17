



















subroutine c815_save_twice()
    implicit none
    integer, save :: n = 0
       ! {error C815 save-stmt}
    n = n + 1
end subroutine





