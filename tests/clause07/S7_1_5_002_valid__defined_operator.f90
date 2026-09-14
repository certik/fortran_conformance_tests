! rule: S7.1.5-002
! covers: defined-derived-operator
! evidence: positive-control
module type_basics_defined_operation
    implicit none
    type :: item
        integer :: payload
    end type item
    interface operator(+)
        module procedure add_items
    end interface
contains
    function add_items(left, right) result(value)
        type(item), intent(in) :: left, right
        type(item) :: value
        value%payload = left%payload + right%payload
    end function add_items
end module type_basics_defined_operation

program type_basics_defined
    use type_basics_defined_operation, only: item, operator(+)
    implicit none
    type(item) :: left, right, value

    left%payload = 2
    right%payload = 3
    value = left + right
    if (value%payload /= 5) error stop 1
end program type_basics_defined
