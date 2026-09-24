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
integer :: u, ios, recl, sample, left, right
sample = 0
inquire(iolength=recl) sample
open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
write(u,rec=2) 202
write(u,rec=1) 101
left = -8001
left = -7001
call check_int('pre-read-1-left', left, -7001)
read(u,rec=1,iostat=ios) left
call check_int('read-record-one-status', ios, 0)
call check_int('read-record-one-value', left, 101)
right = -8002
right = -7002
call check_int('pre-read-2-right', right, -7002)
read(u,rec=2,iostat=ios) right
call check_int('read-record-two-status', ios, 0)
call check_int('read-record-two-value', right, 202)
close(u, status='delete')
call finish_checks(6)
end program p
