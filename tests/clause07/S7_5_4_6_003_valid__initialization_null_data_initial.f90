! rule: S7.5.4.6-003
! covers: initial-status
! evidence: effect
! standard: f2023
module event_types
implicit none
integer :: checks_completed=0
integer, target, save :: original = 7, alternate = 11
type :: record
integer, pointer :: alias => null()
end type
contains
subroutine verify(item)
type(record), intent(in) :: item
if (associated(item%alias)) error stop 1
checks_completed=checks_completed+1
end subroutine
subroutine change(item)
type(record), intent(inout) :: item
item%alias => alternate
end subroutine
subroutine reset(item)
type(record), intent(out) :: item
call verify(item)
end subroutine
end module
program event_witness
use event_types
implicit none
type(record), save :: item
call verify(item)
call change(item)
if (checks_completed /= 1) error stop 20
end program
