





















subroutine c726_local_variable()
    implicit none
    character(3) :: s   ! {error C726 local-variable}
    s = "abc"
end subroutine



















