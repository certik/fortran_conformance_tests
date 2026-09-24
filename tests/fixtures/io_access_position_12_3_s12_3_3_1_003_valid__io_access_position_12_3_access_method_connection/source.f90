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
integer :: u, ios, recl, sample, value, char_units
character(len=10) :: access_name
character(len=1) :: ch
character(len=*), parameter :: fname = 'io_access_position_12_3_connection.dat'
sample = 0
inquire(iolength=recl) sample
inquire(iolength=char_units) ch
open(newunit=u, file=fname, status='replace', access='sequential', form='formatted', action='readwrite')
inquire(unit=u, access=access_name)
call check_char('sequential-connection-access', access_name, 'SEQUENTIAL')
write(u,'(i0)') 37
rewind u
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(u,*,iostat=ios) value
call check_int('sequential-connection-read-status', ios, 0)
call check_int('sequential-connection-read-value', value, 37)
close(u)
open(newunit=u, file=fname, status='replace', access='direct', form='unformatted', recl=recl, action='readwrite')
inquire(unit=u, access=access_name)
call check_char('direct-connection-access', access_name, 'DIRECT    ')
write(u,rec=1) 73
value = -8002
value = -7002
call check_int('pre-read-2-value', value, -7002)
read(u,rec=1,iostat=ios) value
call check_int('direct-connection-read-status', ios, 0)
call check_int('direct-connection-read-value', value, 73)
close(u)
open(newunit=u, file=fname, status='replace', access='stream', form='unformatted', action='readwrite')
inquire(unit=u, access=access_name)
call check_char('stream-connection-access', access_name, 'STREAM    ')
write(u,pos=1 + char_units) 'V'
ch = '!'
ch = '$'
call check_char('pre-read-3-ch', ch, '$')
read(u,pos=1 + char_units,iostat=ios) ch
call check_int('stream-connection-read-status', ios, 0)
call check_char('stream-connection-read-value', ch, 'V')
close(u, status='delete')
call finish_checks(12)
end program p
