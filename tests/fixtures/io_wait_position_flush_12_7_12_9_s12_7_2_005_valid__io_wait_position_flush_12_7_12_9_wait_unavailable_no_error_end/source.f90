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
integer :: closed_unit, ios, err_flag, end_flag
        logical :: opened
        open(newunit=closed_unit, status='scratch', form='formatted')
        close(closed_unit, status='delete')
        inquire(unit=closed_unit, opened=opened)
        call check_false('unavailable-closed-unit', opened)
        ios = -131
        err_flag = -132
        end_flag = -133
        wait(unit=closed_unit, iostat=ios, err=90, end=91)
        call check_int('unavailable-wait-status', ios, 0)
        call check_int('unavailable-wait-no-error-branch', err_flag, -132)
        call check_int('unavailable-wait-no-end-branch', end_flag, -133)
        goto 100
90      err_flag = 0
        goto 100
91      end_flag = 0
100     continue
call finish_checks(4)
end program p
