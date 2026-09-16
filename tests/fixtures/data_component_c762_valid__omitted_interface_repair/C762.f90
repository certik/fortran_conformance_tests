module definitions
implicit none
type :: record
    procedure(), pointer, nopass :: action
end type
end module
