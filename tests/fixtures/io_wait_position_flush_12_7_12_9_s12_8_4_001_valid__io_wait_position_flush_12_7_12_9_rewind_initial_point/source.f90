module io_wait_position_flush_checks
use iso_fortran_env, only: iostat_end, iostat_eor
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, check_false, finish_checks, iostat_end, iostat_eor
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
end module io_wait_position_flush_checks
program p
use io_wait_position_flush_checks
implicit none
integer :: u, ios, value
open(newunit=u, file='iwpf_rewind.dat', status='replace', form='formatted', action='readwrite')
write(u,'(i0)') 801
write(u,'(i0)') 802
rewind u
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(u,*,iostat=ios) value
call check_int('rewind-first-read-status', ios, 0)
call check_int('rewind-first-read-value', value, 801)
value = -8002
value = -7002
call check_int('pre-read-2-value', value, -7002)
read(u,*,iostat=ios) value
call check_int('second-read-status', ios, 0)
call check_int('second-read-value', value, 802)
rewind(unit=u, iostat=ios)
call check_int('rewind-position-status', ios, 0)
value = -8003
value = -7003
call check_int('pre-read-3-value', value, -7003)
read(u,*,iostat=ios) value
call check_int('rewind-reread-status', ios, 0)
call check_int('rewind-reread-value', value, 801)
close(u, status='delete')
call finish_checks(10)
end program p
