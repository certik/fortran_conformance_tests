module type_parameters_kind_expression
    implicit none
    type :: token(k)
        integer, kind :: k
        integer :: payload
    end type token
contains
    subroutine check(n)
        integer, intent(in) :: n
        type(token(kind(0))) :: value
    end subroutine check
end module type_parameters_kind_expression
