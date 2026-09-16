module definitions
implicit none
type :: record
    procedure(integer), pointer :: action
end type
end module
