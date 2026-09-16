module definitions
implicit none
type :: record
    sequence
    integer, public :: payload
    procedure(iface), pointer, public :: action
end type
type(record) :: seed
abstract interface
    subroutine iface(self)
        import :: seed
        typeof(seed), intent(in) :: self
    end subroutine
end interface
end module
