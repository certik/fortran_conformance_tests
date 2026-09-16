module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: act => impl
end type record
contains
subroutine impl()
end subroutine impl
subroutine other()
end subroutine other
end module tbp_defs
