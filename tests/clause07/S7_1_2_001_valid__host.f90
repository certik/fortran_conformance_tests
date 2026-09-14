! rule: S7.1.2-001
! covers: host-derived-name
! evidence: positive-control
program type_basics_host
    implicit none
    type :: item
        integer :: payload
    end type item
    type(item) :: value

    value%payload = 23
    if (read_item(value) /= 23) error stop 1
contains
    integer function read_item(argument) result(payload)
        type(item), intent(in) :: argument
        payload = argument%payload
    end function read_item
end program type_basics_host
