




































subroutine c726_internal_function_result()
    implicit none
    print *, g()
contains
    function g() result(r)
        character(1) :: r   ! {error C726 internal-function-result}
        r = "x"
    end function
end subroutine
