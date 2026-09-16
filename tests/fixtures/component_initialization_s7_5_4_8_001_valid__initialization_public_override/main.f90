program client
use access_provider, only: record
implicit none
type(record) :: item
item%visible=7
if (item%visible /= 7) error stop 1
end program
