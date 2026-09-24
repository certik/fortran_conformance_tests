module io_units_connection_checks
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
end module io_units_connection_checks
program p
use io_units_connection_checks
use iso_fortran_env, only: input_unit, output_unit, error_unit
implicit none
integer :: u, ios, initial_value, changed_value
character(len=4) :: blank_mode
open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')
write(u,'(a)') '1 2'
rewind u
initial_value = -8001
initial_value = -7001
call check_int('pre-read-1-initial_value', initial_value, -7001)
read(u,'(i3)',iostat=ios) initial_value
call check_int('open-established-null-status', ios, 0)
call check_int('open-established-null-value', initial_value, 12)
open(unit=u, blank='zero')
inquire(unit=u, blank=blank_mode)
call check_char('subsequent-open-blank-mode', blank_mode, 'ZERO')
rewind u
changed_value = -8002
changed_value = -7002
call check_int('pre-read-2-changed_value', changed_value, -7002)
read(u,'(i3)',iostat=ios) changed_value
call check_int('subsequent-open-zero-status', ios, 0)
call check_int('subsequent-open-zero-value', changed_value, 102)
close(u, status='delete')
call finish_checks(7)
end program p
