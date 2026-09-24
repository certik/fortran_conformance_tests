module io_open_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_nonzero, check_char, check_true, check_false, finish_checks
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
subroutine check_nonzero(label, actual)
character(*), intent(in) :: label
integer, intent(in) :: actual
if (actual == 0) then
print *, 'CHECK_NONZERO', label, 'ACTUAL', actual
error stop 2
end if
checked = checked + 1
end subroutine check_nonzero
subroutine check_char(label, actual, expected)
character(*), intent(in) :: label
character(*), intent(in) :: actual, expected
if (len(actual) /= len(expected)) then
print *, 'CHECK_CHAR_LEN', label, len(actual), len(expected)
error stop 3
end if
if (actual /= expected) then
print *, 'CHECK_CHAR', label, 'ACTUAL', actual, 'EXPECTED', expected
error stop 4
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
error stop 5
end if
end subroutine finish_checks
end module io_open_checks
program p
use io_open_checks
implicit none
integer :: main_u, sub_u, ios, main_value, sub_value
open(newunit=main_u, file='io_open_main.dat', status='replace', form='formatted', action='readwrite')
write(main_u,'(i0)') 31
rewind main_u
main_value = -8001
main_value = -7001
call check_int('pre-read-1-main_value', main_value, -7001)
read(main_u,*,iostat=ios) main_value
call check_int('main-open-read-status', ios, 0)
call check_int('main-open-read-value', main_value, 31)
call connect_in_subprogram(sub_u)
rewind sub_u
sub_value = -8002
sub_value = -7002
call check_int('pre-read-2-sub_value', sub_value, -7002)
read(sub_u,*,iostat=ios) sub_value
call check_int('subprogram-open-read-status', ios, 0)
call check_int('subprogram-open-read-value', sub_value, 42)
close(main_u, status='delete')
close(sub_u, status='delete')
call finish_checks(6)
contains
subroutine connect_in_subprogram(unit)
integer, intent(out) :: unit
open(newunit=unit, file='io_open_sub.dat', status='replace', form='formatted', action='readwrite')
write(unit,'(i0)') 42
end subroutine connect_in_subprogram
end program p
