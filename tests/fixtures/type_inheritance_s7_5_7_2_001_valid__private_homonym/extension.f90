module extension
use provider, only: parent
implicit none
type, extends(parent) :: child
    integer, public :: hidden
end type
end module
