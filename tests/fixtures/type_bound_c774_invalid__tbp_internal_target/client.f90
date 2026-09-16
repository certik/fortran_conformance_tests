program p
use tbp_provider, only: impl
implicit none
type :: record
contains
procedure, nopass :: act => internal_work
end type record
contains
subroutine internal_work()
end subroutine internal_work
end program p
