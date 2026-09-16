module definitions
use functions, only: extent
implicit none
type :: record
    integer :: field(extent(2))
end type
end module
