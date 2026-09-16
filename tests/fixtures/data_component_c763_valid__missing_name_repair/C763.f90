module definitions
implicit none
type :: record
    integer :: payload
    procedure(iface), pointer, pass(self) :: action
end type
abstract interface
    subroutine iface(tag,self)
        import :: record
        integer, intent(in) :: tag
        class(record), intent(in) :: self
    end subroutine
end interface
end module
