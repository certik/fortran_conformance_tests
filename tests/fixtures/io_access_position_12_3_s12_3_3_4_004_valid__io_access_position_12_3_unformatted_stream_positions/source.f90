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
integer :: u, ios, pos0, char_units, second_pos
character(len=1) :: ch
inquire(iolength=char_units) ch
second_pos = 1 + char_units
open(newunit=u, status='scratch', access='stream', form='unformatted', action='readwrite')
inquire(unit=u, pos=pos0)
call check_true('initial-unformatted-position-positive', pos0 > 0)
call check_int('initial-unformatted-position-one', pos0, 1)
write(u,pos=1) 'Z'
write(u,pos=1) 'A'
write(u,pos=second_pos) 'B'
ch = '!'
ch = '#'
call check_char('pre-read-1-ch', ch, '#')
read(u,pos=1,iostat=ios) ch
call check_int('first-position-status', ios, 0)
call check_char('first-position-value', ch, 'A')
ch = '!'
ch = '@'
call check_char('pre-read-2-ch', ch, '@')
read(u,pos=second_pos,iostat=ios) ch
call check_int('subsequent-position-status', ios, 0)
call check_char('subsequent-position-value', ch, 'B')
close(u, status='delete')
call finish_checks(8)
end program p
