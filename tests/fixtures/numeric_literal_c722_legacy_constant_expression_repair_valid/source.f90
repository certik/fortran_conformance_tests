




















subroutine c722_in_constant_expression()
    implicit none
    real, parameter :: p = 2.0 * 3.0   ! {error C722 constant-expression}
end subroutine
