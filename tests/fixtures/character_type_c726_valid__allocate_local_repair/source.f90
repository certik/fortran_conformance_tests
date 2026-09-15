


























subroutine c726_allocate_local()
    implicit none
    character(:), allocatable :: s
    allocate(character(3) :: s)   ! {error C726 allocate-local}
end subroutine














