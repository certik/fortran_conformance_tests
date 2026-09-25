module io_control_list_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_nonzero, check_char, check_true, finish_checks
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
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, 'EXPECTED', expected
error stop 5
end if
end subroutine finish_checks
end module io_control_list_checks
program p
use io_control_list_checks
implicit none
integer :: us, ud, value
open(newunit=us, status='scratch', form='formatted', access='stream')
write(us,'(A)') '567'
value = -565
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(us,'(I1)',pos=2) value
call check_int('stream-pos-read', value, 6)
close(us)
open(newunit=ud, status='scratch', form='formatted', access='direct', recl=1)
write(ud,'(I1)',rec=1) 7
value = -575
value = -8002
value = -7002
call check_int('pre-read-2-value', value, -7002)
read(ud,'(I1)',rec=1) value
call check_int('direct-rec-read', value, 7)
close(ud)
call finish_checks(4)
end program p
