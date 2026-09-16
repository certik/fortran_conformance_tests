module definitions
implicit none
type :: carrier
    integer, public :: payload
end type
type(carrier) :: a, b
type :: record
    procedure(character(len=2)), pointer, nopass :: action
end type
end module
