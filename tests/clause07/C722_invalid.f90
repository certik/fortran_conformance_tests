! standard: f2023
! profile: absent-real-kind-seven
! C722 (R714) The value of kind-param shall specify an approximation method
! that exists on the processor.
! The profile establishes that kind 7 is absent before these cases are compiled.
subroutine c722_digit_string()
    implicit none
    real :: r
    r = 1.0_7   ! {error C722 digit-string}
end subroutine
subroutine c722_named_constant()
    implicit none
    integer, parameter :: k = 7
    real :: r
    r = 1.0_k   ! {error C722 named-constant}
end subroutine
subroutine c722_exponent_form()
    implicit none
    real :: r
    r = 1.0e0_7   ! {error C722 exponent-form}
end subroutine
subroutine c722_in_constant_expression()
    implicit none
    real, parameter :: p = 2.0_7 * 3.0   ! {error C722 constant-expression}
end subroutine
subroutine c722_in_array_constructor()
    implicit none
    real :: a(2)
    a = [1.0_7, 2.0_7]   ! {error C722 array-constructor}
end subroutine
