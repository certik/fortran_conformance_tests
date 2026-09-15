module provider
implicit none
private
public :: inspect
type :: hidden_record
    integer :: payload
end type
contains
integer function inspect()
    type(hidden_record) :: value
    value = hidden_record(17)
    inspect = value%payload
end function
end module
