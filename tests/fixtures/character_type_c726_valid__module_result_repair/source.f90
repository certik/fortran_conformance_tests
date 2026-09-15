













module c726_module_function_result
    implicit none
contains
    function f() result(r)
        character(3) :: r   ! {error C726 module-function-result}
        r = "abc"
    end function
end module
























