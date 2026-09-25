module io_wait_position_flush_checks
use iso_fortran_env, only: iostat_end, iostat_eor
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, check_false, finish_checks, iostat_end, iostat_eor
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
end module io_wait_position_flush_checks
program p
use io_wait_position_flush_checks
implicit none
integer :: u, ios, pos_after_ab, terminal_pos
character(len=1) :: ch
open(newunit=u, file='iwpf_stream_endfile.dat', status='replace', access='stream', &
     form='unformatted', action='readwrite')
write(u) 'A'
write(u) 'B'
inquire(unit=u, pos=pos_after_ab)
write(u) 'C'
write(u) 'D'
write(u, pos=pos_after_ab) 'X'
inquire(unit=u, pos=terminal_pos)
endfile u
ch = '!'
ch = '#'
call check_char('pre-read-1-ch', ch, '#')
read(u, pos=1, iostat=ios) ch
call check_int('stream-prefix-read-status', ios, 0)
call check_char('stream-prefix-read-value', ch, 'A')
ch = '!'
ch = '@'
call check_char('pre-read-2-ch', ch, '@')
read(u, pos=pos_after_ab, iostat=ios) ch
call check_int('stream-current-minus-one-status', ios, 0)
call check_char('stream-current-minus-one-value', ch, 'X')
ch = '!'
ch = '$'
call check_char('pre-read-3-ch', ch, '$')
read(u, pos=terminal_pos, iostat=ios) ch
call check_int('stream-terminal-read-status', ios, iostat_end)
call check_char('stream-terminal-read-sentinel', ch, '$')
close(u, status='delete')
call finish_checks(9)
end program p
