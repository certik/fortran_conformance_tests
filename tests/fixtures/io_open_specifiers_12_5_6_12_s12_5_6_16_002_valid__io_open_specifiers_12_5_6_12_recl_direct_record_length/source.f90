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
integer :: u, ios, reclen, value
value = 12345
inquire(iolength=reclen) value
open(newunit=u, file='ioos_12_5_6_12_direct.dat', status='replace', &
     access='direct', form='unformatted', recl=reclen, action='readwrite')
write(u, rec=1, iostat=ios) value
call check_int('recl-direct-write-status', ios, 0)
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(u, rec=1, iostat=ios) value
call check_int('recl-direct-read-status', ios, 0)
call check_int('recl-direct-read-value', value, 12345)
close(u, status='delete')
call finish_checks(4)
end program p
