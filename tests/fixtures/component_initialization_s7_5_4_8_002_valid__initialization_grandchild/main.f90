program client
use access_provider, only: record, fill, read_value
implicit none
type(record) :: item
call fill(item)
if (read_value(item) /= 7) error stop 1
end program
