subroutine s15524_real4_to_real8()
    implicit none
    real(4) :: a = 1.0
    call s(a)
contains
    subroutine s(x)
        real(4), intent(in) :: x
    end subroutine
end subroutine
