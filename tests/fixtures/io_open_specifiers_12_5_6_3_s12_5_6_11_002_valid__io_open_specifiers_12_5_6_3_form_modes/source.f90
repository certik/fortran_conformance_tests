module io_open_specifier_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_char, check_true, check_false, finish_checks
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
end module io_open_specifier_checks
program p
use io_open_specifier_checks
implicit none
integer :: u, ios, recl, value
character(len=11) :: form_mode
value = 0
inquire(iolength=recl) value
open(newunit=u, file='ioos_form_seq.dat', status='replace', &
     access='sequential', action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('form-default-sequential', form_mode, 'FORMATTED  ')
close(u, status='delete')
open(newunit=u, file='ioos_form_direct.dat', status='replace', &
     access='direct', recl=recl, action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('form-default-direct', form_mode, 'UNFORMATTED')
close(u, status='delete')
open(newunit=u, file='ioos_form_stream.dat', status='replace', &
     access='stream', action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('form-default-stream', form_mode, 'UNFORMATTED')
close(u, status='delete')
open(newunit=u, status='scratch', form='formatted', action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('form-explicit-formatted-token', form_mode, 'FORMATTED  ')
write(u,'(i0)') 511
rewind u
value = -8001
value = -7001
call check_int('pre-read-1-value', value, -7001)
read(u,*,iostat=ios) value
call check_int('form-formatted-read-status', ios, 0)
call check_int('form-formatted-read-value', value, 511)
close(u, status='delete')
open(newunit=u, file='ioos_form_existing.dat', status='replace', &
     form='formatted', action='readwrite')
write(u,'(i0)') 512
close(u)
open(newunit=u, file='ioos_form_existing.dat', status='old', &
     form='formatted', action='read')
inquire(unit=u, form=form_mode)
call check_char('form-existing-formatted-token', form_mode, 'FORMATTED  ')
value = -8002
value = -7002
call check_int('pre-read-2-value', value, -7002)
read(u,*,iostat=ios) value
call check_int('form-existing-read-status', ios, 0)
call check_int('form-existing-read-value', value, 512)
close(u, status='delete')
open(newunit=u, file='ioos_form_unformatted.dat', status='replace', &
     form='unformatted', action='readwrite')
inquire(unit=u, form=form_mode)
call check_char('form-new-unformatted-token', form_mode, 'UNFORMATTED')
write(u) 513
rewind u
value = -8003
value = -7003
call check_int('pre-read-3-value', value, -7003)
read(u,iostat=ios) value
call check_int('form-unformatted-read-status', ios, 0)
call check_int('form-unformatted-read-value', value, 513)
close(u, status='delete')
call finish_checks(15)
end program p
