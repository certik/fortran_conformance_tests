module access_provider
implicit none
type :: record
  private
  integer :: hidden
end type
contains
subroutine fill(item)
  type(record), intent(out) :: item
  item%hidden=7
end subroutine
integer function read_value(item)
  type(record), intent(in) :: item
  read_value=item%hidden
end function
end module
