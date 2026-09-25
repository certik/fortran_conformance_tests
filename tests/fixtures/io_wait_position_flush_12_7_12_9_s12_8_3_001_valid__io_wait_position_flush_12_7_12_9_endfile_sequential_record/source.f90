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
integer :: u, ios
character(len=1) :: rec
open(newunit=u, file='iwpf_endfile_seq.dat', status='replace', form='formatted', action='readwrite')
write(u,'(a)') 'A'
write(u,'(a)') 'B'
endfile u
rewind u
rec = '!'
rec = '#'
call check_char('pre-read-1-rec', rec, '#')
read(u,'(a)',iostat=ios) rec
call check_int('endfile-first-status', ios, 0)
call check_char('endfile-first-record', rec, 'A')
rec = '!'
rec = '@'
call check_char('pre-read-2-rec', rec, '@')
read(u,'(a)',iostat=ios) rec
call check_int('endfile-second-status', ios, 0)
call check_char('endfile-second-record', rec, 'B')
rec = '!'
rec = '$'
call check_char('pre-read-3-rec', rec, '$')
read(u,'(a)',iostat=ios) rec
call check_int('endfile-status', ios, iostat_end)
call check_char('endfile-read-preserves-sentinel', rec, '$')
close(u, status='delete')
open(newunit=u, file='iwpf_endfile_last.dat', status='replace', form='formatted', action='readwrite')
write(u,'(a)') 'D'
write(u,'(a)') 'E'
write(u,'(a)') 'F'
rewind u
rec = '!'
rec = '%'
call check_char('pre-read-4-rec', rec, '%')
read(u,'(a)',iostat=ios) rec
call check_int('last-record-prefix-status', ios, 0)
call check_char('last-record-prefix-value', rec, 'D')
endfile u
rewind u
rec = '!'
rec = '&'
call check_char('pre-read-5-rec', rec, '&')
read(u,'(a)',iostat=ios) rec
call check_int('last-record-reread-status', ios, 0)
call check_char('last-record-reread-value', rec, 'D')
rec = '!'
rec = '?'
call check_char('pre-read-6-rec', rec, '?')
read(u,'(a)',iostat=ios) rec
call check_int('last-record-end-status', ios, iostat_end)
call check_char('last-record-end-sentinel', rec, '?')
close(u, status='delete')
call finish_checks(18)
end program p
