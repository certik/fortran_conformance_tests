module io_access_position_checks
use iso_fortran_env, only: iostat_end
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, finish_checks, iostat_end
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
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 4
end if
end subroutine finish_checks
end module io_access_position_checks
program p
use io_access_position_checks
implicit none
integer :: u, ios
character(len=3) :: first, second
open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
write(u,'(a)') 'ABC'
write(u,'(a)') 'XYZ'
rewind u
first = '!!!'
first = '###'
call check_char('pre-read-1-first', first, '###')
read(u,'(a)',iostat=ios) first
call check_int('formatted-stream-first-record-status', ios, 0)
call check_char('formatted-stream-first-record-value', first, 'ABC')
second = '!!!'
second = '@@@'
call check_char('pre-read-2-second', second, '@@@')
read(u,'(a)',iostat=ios) second
call check_int('formatted-stream-second-record-status', ios, 0)
call check_char('formatted-stream-second-record-value', second, 'XYZ')
close(u, status='delete')
call finish_checks(6)
end program p
