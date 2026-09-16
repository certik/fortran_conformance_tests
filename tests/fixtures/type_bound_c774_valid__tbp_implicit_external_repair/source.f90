module tbp_defs
implicit none
interface
subroutine work()
end subroutine work
end interface
type :: record
contains
procedure, nopass :: act => work
end type record
end module tbp_defs
subroutine work()
end subroutine work
