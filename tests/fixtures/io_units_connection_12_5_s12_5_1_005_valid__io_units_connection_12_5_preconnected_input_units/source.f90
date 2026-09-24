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
integer :: star_value, input_value, bare_value, ios
character(len=8) :: internal_star, internal_input, internal_bare
internal_star = '91      '
internal_input = '92      '
internal_bare = '93      '
star_value = -8001
star_value = -7001
call check_int('pre-read-1-star_value', star_value, -7001)
read(*,*,iostat=ios) star_value
call check_int('read-star-status', ios, 0)
call check_int('read-star-value', star_value, 31)
input_value = -8002
input_value = -7002
call check_int('pre-read-2-input_value', input_value, -7002)
read(input_unit,*,iostat=ios) input_value
call check_int('read-input-unit-status', ios, 0)
call check_int('read-input-unit-value', input_value, 32)
bare_value = -8003
bare_value = -7003
call check_int('pre-read-3-bare_value', bare_value, -7003)
read *, bare_value
call check_int('read-bare-value', bare_value, 33)
call finish_checks(8)
end program p
