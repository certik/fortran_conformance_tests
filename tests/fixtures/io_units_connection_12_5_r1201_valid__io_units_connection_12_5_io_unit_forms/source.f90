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
integer :: u, ios, external_value, internal_value
character(len=8) :: internal_file, alternate_file
internal_file = '62      '
alternate_file = '91      '
open(newunit=u, status='scratch', form='formatted', action='readwrite')
write(u,'(i0)') 61
rewind u
external_value = -8001
external_value = -7001
call check_int('pre-read-1-external_value', external_value, -7001)
read(u,*,iostat=ios) external_value
call check_int('file-unit-number-form-status', ios, 0)
call check_int('file-unit-number-form-value', external_value, 61)
internal_value = -8002
internal_value = -7002
call check_int('pre-read-2-internal_value', internal_value, -7002)
read(internal_file,*,iostat=ios) internal_value
call check_int('internal-file-variable-form-status', ios, 0)
call check_int('internal-file-variable-form-value', internal_value, 62)
write(*,'(a)') 'R1201-STAR-OUTPUT'
close(u, status='delete')
call finish_checks(6)
end program p
