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
integer :: u, other, ios, msg_probe, err_probe
        character(len=1) :: rec
        character(len=32) :: msg
        open(newunit=u, file='iwpf_r1227.dat', status='replace', form='formatted', action='readwrite')
        open(newunit=other, file='iwpf_r1227_other.dat', status='replace', form='formatted', action='readwrite')
        write(u,'(a)') 'A'
        write(u,'(a)') 'B'
        write(other,'(a)') 'X'
        write(other,'(a)') 'Y'
        rewind u
        rec = '!'
        rec = '#'
        call check_char('pre-read-1-rec', rec, '#')
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-first-read-status', ios, 0)
        call check_char('r1227-first-read-value', rec, 'A')
        backspace(unit=u)
        rec = '!'
        rec = '@'
        call check_char('pre-read-2-rec', rec, '@')
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-unit-specifier-read-status', ios, 0)
        call check_char('r1227-unit-specifier-read-value', rec, 'A')
        rec = '!'
        rec = '$'
        call check_char('pre-read-3-rec', rec, '$')
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-second-read-status', ios, 0)
        call check_char('r1227-second-read-value', rec, 'B')
        ios = -123
        backspace(unit=u, iostat=ios)
        call check_int('r1227-iostat-specifier-status', ios, 0)
        rec = '!'
        rec = '%'
        call check_char('pre-read-4-rec', rec, '%')
        read(u,'(a)',iostat=ios) rec
        call check_int('r1227-iostat-reread-status', ios, 0)
        call check_char('r1227-iostat-reread-value', rec, 'B')
        msg = '################################'
        msg_probe = -456
        rewind(unit=u, iomsg=msg)
        call check_int('r1227-iomsg-probe-unchanged', msg_probe, -456)
        err_probe = -789
        rewind(unit=u, err=90)
        call check_int('r1227-err-branch-not-taken', err_probe, -789)
        goto 100
90      err_probe = 0
100     continue
        close(u, status='delete')
        close(other, status='delete')
call finish_checks(15)
end program p
