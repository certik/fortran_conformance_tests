module definitions
implicit none
type :: good_type
integer :: payload
end type
type :: record
    type(good_type) :: field
end type
type :: later_type
integer :: payload
end type
end module
