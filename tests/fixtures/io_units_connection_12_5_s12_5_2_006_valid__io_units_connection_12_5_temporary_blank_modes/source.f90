module io_units_connection_checks
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
end module io_units_connection_checks
program p
use io_units_connection_checks
use iso_fortran_env, only: input_unit, output_unit, error_unit
implicit none
integer :: u, ios, keyword_value, reset_value, bz_value, bn_value
open(newunit=u, status='scratch', form='formatted', action='readwrite', blank='null')
write(u,'(a)') '1 2'
write(u,'(a)') '1 2'
write(u,'(a)') '1 21 2'
rewind u
keyword_value = -8001
keyword_value = -7001
call check_int('pre-read-1-keyword_value', keyword_value, -7001)
read(u,'(i3)',blank='zero',iostat=ios) keyword_value
call check_int('keyword-temporary-status', ios, 0)
call check_int('keyword-temporary-value', keyword_value, 102)
reset_value = -8002
reset_value = -7002
call check_int('pre-read-2-reset_value', reset_value, -7002)
read(u,'(i3)',iostat=ios) reset_value
call check_int('mode-reset-status', ios, 0)
call check_int('mode-reset-value', reset_value, 12)
bz_value = -7101
call check_int('pre-read-bz-value', bz_value, -7101)
bn_value = -7102
call check_int('pre-read-bn-value', bn_value, -7102)
read(u,'(bz,i3,bn,i3)',iostat=ios) bz_value, bn_value
call check_int('edit-descriptor-status', ios, 0)
call check_int('edit-descriptor-bz-value', bz_value, 102)
call check_int('edit-descriptor-bn-value', bn_value, 12)
close(u, status='delete')
call finish_checks(11)
end program p
