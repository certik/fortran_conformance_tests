module definitions
implicit none
type :: carrier
    integer, public :: payload
end type
type(carrier) :: a, b
type :: record
    procedure(character(len=merge(2,3,same_type_as(a,b)))), pointer, nopass :: action
end type
end module
