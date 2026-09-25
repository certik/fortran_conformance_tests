module io_open_specifier_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, check_false, finish_checks
contains
subroutine fail(label)
character(*), intent(in) :: label
print *, 'CHECK_FAILED', label
error stop 99
end subroutine fail
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
print *, 'CHECK_INT', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 1
end if
checked = checked + 1
end subroutine check_int
subroutine check_char(label, actual, expected)
character(*), intent(in) :: label
character(*), intent(in) :: actual, expected
if (len(actual) /= len(expected)) then
print *, 'CHECK_CHAR_LEN', label, len(actual), len(expected)
error stop 2
end if
if (actual /= expected) then
print *, 'CHECK_CHAR', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 3
end if
checked = checked + 1
end subroutine check_char
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) call fail(label)
checked = checked + 1
end subroutine check_true
subroutine check_false(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (actual) call fail(label)
checked = checked + 1
end subroutine check_false
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 4
end if
end subroutine finish_checks
end module io_open_specifier_checks
program p
use io_open_specifier_checks
implicit none
integer :: u, recl, value
character(len=11) :: form_mode
value = 0
inquire(iolength=recl) value
open(newunit=u, status='scratch', access='sequential', action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('sequential-default-formatted', form_mode, 'FORMATTED  ')
close(u, status='delete')
open(newunit=u, status='scratch', access='direct', recl=recl, action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('direct-default-unformatted', form_mode, 'UNFORMATTED')
close(u, status='delete')
open(newunit=u, status='scratch', access='stream', action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('stream-default-unformatted', form_mode, 'UNFORMATTED')
close(u, status='delete')
call finish_checks(3)
end program p
