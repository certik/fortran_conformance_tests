module constructor_types
implicit none
abstract interface
subroutine action_interface()
end subroutine action_interface
end interface
type :: holder
integer, pointer :: p=>null()
procedure(action_interface), pointer, nopass :: action=>null()
end type holder
contains
subroutine worker()
end subroutine worker
end module constructor_types
program constructor_case
use constructor_types
implicit none
type(holder) :: value
integer, target :: datum
datum=17
value=holder(p=worker)
end program constructor_case
