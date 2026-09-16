program client
use access_provider, only: record
implicit none
type(record) :: item
item%value=7
if (item%value /= 7) error stop 1
end program
