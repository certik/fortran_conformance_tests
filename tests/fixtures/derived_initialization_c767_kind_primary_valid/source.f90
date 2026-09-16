module component_definition
implicit none
type :: record(extent)
integer, kind :: extent
integer :: values(extent) = 3
end type
end module
