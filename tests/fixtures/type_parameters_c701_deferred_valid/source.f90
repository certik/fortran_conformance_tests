module type_parameters_kind_deferred
    implicit none
    type :: token(k)
        integer, kind :: k = kind(0)
        integer :: payload
    end type token
contains
    subroutine check(value)
        type(token(kind(0))), pointer, intent(in) :: value
    end subroutine check
end module type_parameters_kind_deferred
