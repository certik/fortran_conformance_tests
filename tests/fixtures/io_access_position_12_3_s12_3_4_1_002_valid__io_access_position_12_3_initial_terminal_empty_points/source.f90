module io_access_position_checks
use iso_fortran_env, only: iostat_end
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, finish_checks, iostat_end
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
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 4
end if
end subroutine finish_checks
end module io_access_position_checks
program p
use io_access_position_checks
implicit none
integer :: u, empty_u, ios, value
open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
write(u,'(i0)') 41
write(u,'(i0)') 42
rewind u
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(u,*,iostat=ios) value
call check_int('initial-point-next-status', ios, 0)
call check_int('initial-point-next-value', value, 41)
value = -8002
value = -7002
call check_int('pre-read-2-value', value, -7002)
read(u,*,iostat=ios) value
call check_int('last-record-status', ios, 0)
call check_int('last-record-value', value, 42)
read(u,*,iostat=ios)
call check_int('terminal-point-end-status', ios, iostat_end)
close(u, status='delete')
open(newunit=empty_u, status='scratch', access='sequential', form='formatted', action='readwrite')
read(empty_u,*,iostat=ios)
call check_int('empty-initial-terminal-status', ios, iostat_end)
close(empty_u, status='delete')
call finish_checks(8)
end program p
