! rule: S7.5.4.6-003
! covers: local-entry
! evidence: effect
! standard: f2023
module event_types
implicit none
integer :: checks_completed=0
abstract interface
integer function calculation(x)
integer, intent(in) :: x
end function
end interface
type :: record
procedure(calculation), pointer, nopass :: action => null()
end type
contains
integer function original(x)
integer, intent(in) :: x
original = x+3
end function
integer function alternate(x)
integer, intent(in) :: x
alternate = x+5
end function
subroutine verify(item)
type(record), intent(in) :: item
if (associated(item%action)) error stop 1
checks_completed=checks_completed+1
end subroutine
subroutine change(item)
type(record), intent(inout) :: item
item%action => alternate
end subroutine
subroutine reset(item)
type(record), intent(out) :: item
call verify(item)
end subroutine
end module
program event_witness
use event_types
implicit none

call visit()
call visit()
if (checks_completed /= 2) error stop 20
contains
subroutine visit()
type(record) :: item
call verify(item)
call change(item)
end subroutine

end program
