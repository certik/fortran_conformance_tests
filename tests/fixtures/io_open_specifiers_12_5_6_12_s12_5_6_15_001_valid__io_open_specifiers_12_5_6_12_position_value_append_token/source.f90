module io_open_specifier_12_5_6_12_checks
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
end module io_open_specifier_12_5_6_12_checks
program p
use io_open_specifier_12_5_6_12_checks
use iso_fortran_env, only: input_unit, output_unit, error_unit, iostat_eor
implicit none
integer :: u
character(len=8) :: pos_mode
open(newunit=u, file='ioos_12_5_6_12_pos_token.dat', status='replace', &
     access='stream', form='unformatted', action='readwrite')
write(u, pos=1) 'A'
close(u)
open(newunit=u, file='ioos_12_5_6_12_pos_token.dat', status='old', &
     access='stream', form='unformatted', action='readwrite', position='append')
pos_mode = '########'
inquire(unit=u, position=pos_mode)
call check_char('position-append-token', pos_mode, 'APPEND  ')
close(u, status='delete')
call finish_checks(1)
end program p
