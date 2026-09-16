module definitions
implicit none
type :: record
    procedure(integer), pointer, nopass :: action
end type
end module
