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
integer :: u, ios, char_units, next_pos
character(len=3) :: rec
character(len=1) :: ch
inquire(iolength=char_units) ch
next_pos = 1 + char_units
open(newunit=u, status='scratch', access='stream', form='formatted', action='readwrite')
write(u,'(a)') 'ABC'
rewind u
rec = '!!!'
rec = '###'
call check_char('pre-read-1-rec', rec, '###')
read(u,'(a)',iostat=ios) rec
call check_int('formatted-stream-record-status', ios, 0)
call check_char('formatted-stream-record-value', rec, 'ABC')
close(u, status='delete')
open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
write(u,pos=1) 'U'
write(u,pos=next_pos) 'V'
ch = '!'
ch = '@'
call check_char('pre-read-2-ch', ch, '@')
read(u,pos=1,iostat=ios) ch
call check_int('unformatted-stream-position-status', ios, 0)
call check_char('unformatted-stream-position-value', ch, 'U')
close(u, status='delete')
call finish_checks(6)
end program p
