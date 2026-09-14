subroutine s15524_function_result_kind()
    implicit none
    real(8) :: y
    y = f(1.0)
contains
    real(8) function f(x)
        real(8), intent(in) :: x
        f = x
    end function
end subroutine
