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
integer :: u
character(len=8) :: blank_mode, decimal_mode, delim_mode
open(newunit=u, file='io_open_limited_values.dat', status='replace', form='formatted', &
     blank='zErO   ', decimal='cOmMa  ', delim='qUoTe  ')
blank_mode = '########'
decimal_mode = '########'
delim_mode = '########'
inquire(unit=u, blank=blank_mode, decimal=decimal_mode, delim=delim_mode)
call check_char('limited-blank-zero', blank_mode, 'ZERO    ')
call check_char('trailing-decimal-comma', decimal_mode, 'COMMA   ')
call check_char('case-delim-quote', delim_mode, 'QUOTE   ')
close(u, status='delete')
call finish_checks(3)
end program p
