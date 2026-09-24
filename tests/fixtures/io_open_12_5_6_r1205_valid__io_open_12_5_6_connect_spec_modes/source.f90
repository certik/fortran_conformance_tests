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
integer :: u, ios
logical :: opened
character(len=28) :: name
character(len=12) :: access, action, blank, decimal, delim, encoding, form, pad, round_mode, sign_mode
u = 71
ios = -91
open(unit=u, file='io_open_connect_modes.dat', status='replace', access='sequential', &
     form='formatted', action='readwrite', blank='zero', decimal='comma', delim='quote', &
     encoding='default', pad='no', round='up', sign='plus', iostat=ios)
call check_int('connect-spec-iostat-zero', ios, 0)
opened = .false.
name = '############################'
access = '############'
action = '############'
blank = '############'
decimal = '############'
delim = '############'
encoding = '############'
form = '############'
pad = '############'
round_mode = '############'
sign_mode = '############'
inquire(unit=u, opened=opened, name=name, access=access, action=action, blank=blank, &
        decimal=decimal, delim=delim, encoding=encoding, form=form, pad=pad, &
        round=round_mode, sign=sign_mode)
call check_true('connect-spec-unit-opened', opened)
call check_char('connect-spec-file-name', name, 'io_open_connect_modes.dat   ')
call check_char('connect-spec-access', access, 'SEQUENTIAL  ')
call check_char('connect-spec-action', action, 'READWRITE   ')
call check_char('connect-spec-blank', blank, 'ZERO        ')
call check_char('connect-spec-decimal', decimal, 'COMMA       ')
call check_char('connect-spec-delim', delim, 'QUOTE       ')
call check_char('connect-spec-encoding', encoding, 'DEFAULT     ')
call check_char('connect-spec-form', form, 'FORMATTED   ')
call check_char('connect-spec-pad', pad, 'NO          ')
call check_char('connect-spec-round', round_mode, 'UP          ')
call check_char('connect-spec-sign', sign_mode, 'PLUS        ')
close(u, status='delete')
call finish_checks(13)
end program p
