subroutine s15524_literal_real4_to_real8()
    implicit none
    call s(1.0_8)
contains
    subroutine s(x)
        real(8), intent(in) :: x
    end subroutine
end subroutine
