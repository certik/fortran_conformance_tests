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
integer :: u, unit_number, file_number
logical :: unit_opened, file_opened, unit_exists, file_exists, unit_named, file_named
character(len=20) :: unit_name, file_name
open(newunit=u, file='iouc_12_5_status.dat', status='replace', form='formatted', action='readwrite')
unit_opened = .false.
file_opened = .false.
unit_exists = .false.
file_exists = .false.
unit_named = .false.
file_named = .false.
unit_number = 0
file_number = 0
unit_name = '####################'
file_name = '@@@@@@@@@@@@@@@@@@@@'
inquire(unit=u, opened=unit_opened, exist=unit_exists, number=unit_number, named=unit_named, name=unit_name)
inquire(file='iouc_12_5_status.dat', opened=file_opened, exist=file_exists, &
        number=file_number, named=file_named, name=file_name)
call check_true('unit-opened', unit_opened)
call check_true('file-opened', file_opened)
call check_true('unit-exists', unit_exists)
call check_true('file-exists', file_exists)
call check_int('unit-number', unit_number, u)
call check_int('file-number', file_number, u)
call check_true('unit-named', unit_named)
call check_true('file-named', file_named)
call check_char('unit-name', unit_name, 'iouc_12_5_status.dat')
call check_char('file-name', file_name, 'iouc_12_5_status.dat')
close(u, status='delete')
unit_opened = .true.
inquire(unit=u, opened=unit_opened)
call check_false('unit-not-opened-after-close', unit_opened)
call finish_checks(11)
end program p
