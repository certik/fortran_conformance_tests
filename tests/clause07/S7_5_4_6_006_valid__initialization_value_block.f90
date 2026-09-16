! rule: S7.5.4.6-006
! covers: block-entry-value
! evidence: effect
! standard: f2023
module event_types
implicit none
integer :: checks_completed=0
type :: record
integer :: value = 3
end type
contains
subroutine verify(item)
type(record), intent(in) :: item
if (item%value /= 3) error stop 1
checks_completed=checks_completed+1
end subroutine
subroutine change(item)
type(record), intent(inout) :: item
item%value = 9
end subroutine
subroutine reset(item)
type(record), intent(out) :: item
call verify(item)
end subroutine
end module
program event_witness
use event_types
implicit none
integer :: iteration
do iteration=1,2
block
type(record) :: item
call verify(item)
call change(item)
end block
end do
if (checks_completed /= 2) error stop 20
end program
