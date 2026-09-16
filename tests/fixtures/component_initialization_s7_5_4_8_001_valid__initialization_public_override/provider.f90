module access_provider
implicit none
type :: record
  private
  integer :: hidden
  integer, public :: visible
end type
end module
