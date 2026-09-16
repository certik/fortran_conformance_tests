module tbp_defs
implicit none
external :: work
type :: record
contains
procedure, nopass :: act => work
end type record
end module tbp_defs
subroutine work()
end subroutine work
