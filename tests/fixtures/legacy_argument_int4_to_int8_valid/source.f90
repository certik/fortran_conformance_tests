subroutine s15524_int4_to_int8()
    implicit none
    integer(4) :: n = 1
    call s(n)
contains
    subroutine s(x)
        integer(4), intent(in) :: x
    end subroutine
end subroutine
