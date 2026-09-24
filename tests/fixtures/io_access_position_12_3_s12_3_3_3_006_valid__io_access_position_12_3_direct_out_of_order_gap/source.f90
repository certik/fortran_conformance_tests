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
integer :: u, ios, recl, sample, value
sample = 0
inquire(iolength=recl) sample
open(newunit=u, status='scratch', access='direct', form='unformatted', recl=recl, action='readwrite')
write(u,rec=3) 303
write(u,rec=1) 101
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(u,rec=1,iostat=ios) value
call check_int('out-of-order-lower-record-status', ios, 0)
call check_int('out-of-order-lower-record-value', value, 101)
value = -8002
value = -7002
call check_int('pre-read-2-value', value, -7002)
read(u,rec=3,iostat=ios) value
call check_int('gap-written-record-status', ios, 0)
call check_int('gap-written-record-value', value, 303)
value = -8003
value = -7003
call check_int('pre-read-3-value', value, -7003)
read(u,rec=3,iostat=ios) value
call check_int('written-record-read-status', ios, 0)
call check_int('written-record-read-value', value, 303)
close(u, status='delete')
call finish_checks(9)
end program p
