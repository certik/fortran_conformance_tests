! rule: S7.5.4.6-005
! covers: allocation-without-source
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
procedure(calculation), pointer, nopass :: action => original
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
if (.not.associated(item%action,original)) error stop 1
if (item%action(4) /= 7) error stop 2
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
type(record), pointer :: item => null()
integer :: stat, iteration
do iteration=1,2
allocate(item,stat=stat)
if (stat /= 0) error stop 10
if (.not.associated(item)) error stop 12
call verify(item)
call change(item)
deallocate(item,stat=stat)
if (stat /= 0) error stop 11
end do
if (checks_completed /= 2) error stop 20
end program
