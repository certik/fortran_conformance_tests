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
integer :: u, ios
character(len=2) :: part
character(len=5) :: whole
open(newunit=u, file='iwpf_back_current.dat', status='replace', form='formatted', action='readwrite')
write(u,'(a)') 'ABCDE'
rewind u
part = '!!'
part = '##'
call check_char('pre-read-1-part', part, '##')
read(u,'(a2)',advance='no',iostat=ios) part
call check_int('nonadvancing-part-status', ios, 0)
call check_char('nonadvancing-part-value', part, 'AB')
backspace u
whole = '!!!!!'
whole = '@@@@@'
call check_char('pre-read-2-whole', whole, '@@@@@')
read(u,'(a)',iostat=ios) whole
call check_int('backspace-current-status', ios, 0)
call check_char('backspace-current-value', whole, 'ABCDE')
close(u, status='delete')
call finish_checks(6)
end program p
