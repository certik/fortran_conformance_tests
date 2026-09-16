module tbp_defs
use tbp_provider, only: local_impl => impl
implicit none
type :: record
contains
procedure, nopass :: act => local_impl
end type record
end module tbp_defs
