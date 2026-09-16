program client
use access_provider, only: record, fill, read_value
implicit none
type(record) :: item, copied
call fill(item)
copied=item
if (read_value(copied) /= 7) error stop 1
end program
