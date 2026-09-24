module io_open_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_nonzero, check_char, check_true, check_false, finish_checks
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
subroutine check_nonzero(label, actual)
character(*), intent(in) :: label
integer, intent(in) :: actual
if (actual == 0) then
print *, 'CHECK_NONZERO', label, 'ACTUAL', actual
error stop 2
end if
checked = checked + 1
end subroutine check_nonzero
subroutine check_char(label, actual, expected)
character(*), intent(in) :: label
character(*), intent(in) :: actual, expected
if (len(actual) /= len(expected)) then
print *, 'CHECK_CHAR_LEN', label, len(actual), len(expected)
error stop 3
end if
if (actual /= expected) then
print *, 'CHECK_CHAR', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 4
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
error stop 5
end if
end subroutine finish_checks
end module io_open_checks
program p
use io_open_checks
implicit none
integer :: u, other, ios, first, second
open(newunit=other, file='io_open_position_other.dat', status='replace', form='formatted', action='readwrite')
write(other,'(i0)') 333
close(other)
open(newunit=u, file='io_open_position_same.dat', status='replace', form='formatted', action='readwrite')
write(u,'(i0)') 111
write(u,'(i0)') 222
rewind u
first = -8001
first = -7001
call check_int('pre-read-1-first', first, -7001)
read(u,*,iostat=ios) first
call check_int('position-first-status', ios, 0)
call check_int('position-first-value', first, 111)
open(unit=u, file='io_open_position_same.dat', status='old', iostat=ios)
call check_int('position-open-status', ios, 0)
second = -8002
second = -7002
call check_int('pre-read-2-second', second, -7002)
read(u,*,iostat=ios) second
call check_int('position-second-status', ios, 0)
call check_int('position-second-value', second, 222)
close(u, status='delete')
open(newunit=other, file='io_open_position_other.dat', status='old', form='formatted')
close(other, status='delete')
call finish_checks(7)
end program p
