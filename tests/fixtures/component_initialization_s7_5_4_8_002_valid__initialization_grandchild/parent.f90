module access_provider
implicit none
type :: record
  private
  integer :: hidden
end type
interface
  module subroutine fill(item)
    type(record), intent(out) :: item
  end subroutine
  module integer function read_value(item)
    type(record), intent(in) :: item
  end function
end interface
end module
