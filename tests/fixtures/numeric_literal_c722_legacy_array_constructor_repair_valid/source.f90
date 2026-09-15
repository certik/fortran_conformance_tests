
























subroutine c722_in_array_constructor()
    implicit none
    real :: a(2)
    a = [1.0, 2.0]   ! {error C722 array-constructor}
end subroutine
