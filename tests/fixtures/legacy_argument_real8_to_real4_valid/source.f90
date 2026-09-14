subroutine s15524_real8_to_real4()
    implicit none
    real(8) :: a = 1.0d0
    call s(a)
contains
    subroutine s(x)
        real(8), intent(in) :: x
    end subroutine
end subroutine
