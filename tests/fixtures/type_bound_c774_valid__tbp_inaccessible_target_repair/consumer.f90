module tbp_defs
use tbp_provider
implicit none
type :: record
contains
procedure, nopass :: act => impl
end type record
end module tbp_defs
