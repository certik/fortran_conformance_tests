module definitions
implicit none
type :: good_type
integer :: payload
end type
type :: record
    type(later_type), pointer :: field
end type
type :: later_type
integer :: payload
end type
end module
