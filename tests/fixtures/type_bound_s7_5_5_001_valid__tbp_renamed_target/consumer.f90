module tbp_consumer
use tbp_provider, only: local_name => provider_value
implicit none
type :: record
integer :: payload
contains
procedure, nopass :: local_name
procedure, nopass :: explicit_alias => local_name
end type record
end module tbp_consumer
