submodule(tbp_ancestor) tbp_descendant
implicit none
type :: record
contains
private
end type record
contains
module procedure anchor
end procedure anchor
end submodule tbp_descendant
