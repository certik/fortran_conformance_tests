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
integer :: u, empty_u, ios, first, middle, last, value
open(newunit=u, status='scratch', access='sequential', form='formatted', action='readwrite')
write(u,'(i0)') 11
write(u,'(i0)') 22
write(u,'(i0)') 33
rewind u
first = -8001
first = -7001
call check_int('pre-read-1-first', first, -7001)
read(u,*,iostat=ios) first
call check_int('initial-next-status', ios, 0)
call check_int('initial-next-value', first, 11)
middle = -8002
middle = -7002
call check_int('pre-read-2-middle', middle, -7002)
read(u,*,iostat=ios) middle
call check_int('between-next-status', ios, 0)
call check_int('between-next-value', middle, 22)
last = -8003
last = -7003
call check_int('pre-read-3-last', last, -7003)
read(u,*,iostat=ios) last
call check_int('last-record-status', ios, 0)
call check_int('last-record-value', last, 33)
read(u,*,iostat=ios)
call check_int('terminal-no-next-status', ios, iostat_end)
close(u, status='delete')
open(newunit=empty_u, status='scratch', access='sequential', form='formatted', action='readwrite')
read(empty_u,*,iostat=ios)
call check_int('empty-no-next-status', ios, iostat_end)
close(empty_u, status='delete')
call finish_checks(11)
end program p
