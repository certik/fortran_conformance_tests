module definitions
implicit none
type :: good_parent
end type
type, extends(good_parent) :: child
integer :: payload
end type
type :: later
end type
end module
