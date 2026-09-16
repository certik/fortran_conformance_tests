program client
use access_provider, only: record
implicit none
type(record) :: item
item=record(hidden=7)
end program
