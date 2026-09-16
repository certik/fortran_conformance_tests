module definitions
implicit none
type :: c_ptr
integer :: payload
end type
type :: c_funptr
integer :: payload
end type
type :: team_type
integer :: payload
end type
type :: record
    type(c_ptr), allocatable :: c_ptr_field[:]
type(c_funptr), allocatable :: c_funptr_field[:]
type(team_type), allocatable :: team_type_field[:]
end type
end module
