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
integer :: u, ios, pos
character(len=10) :: delim_mode
character(len=30) :: line
character(len=3) :: ch
namelist /grp/ ch
open(newunit=u, status='scratch', form='formatted', action='readwrite')
inquire(unit=u, delim=delim_mode)
call check_char('delim-default-none-token', delim_mode, 'NONE      ')
close(u, status='delete')
open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='quote')
write(u,*) 'A"B'
rewind u
line = '##############################'
call check_char('pre-read-list-line', line, '##############################')
read(u,'(a)',iostat=ios) line(1:len(line))
call check_int('delim-quote-list-status', ios, 0)
pos = index(line, '"')
call check_true('delim-quote-list-opening', pos > 0)
call check_int('delim-quote-list-substring-len', len(line(pos:pos+5)), 6)
call check_char('delim-quote-list-substring', line(pos:pos+5), '"A""B"')
close(u, status='delete')
ch = 'A''B'
open(newunit=u, status='scratch', form='formatted', action='readwrite', delim='none')
open(unit=u, delim='apostrophe')
inquire(unit=u, delim=delim_mode)
call check_char('delim-changeable-apostrophe-token', delim_mode, 'APOSTROPHE')
write(u,nml=grp)
rewind u
line = '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@'
call check_char('pre-read-namelist-header', line, '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
read(u,'(a)',iostat=ios) line(1:len(line))
call check_int('delim-namelist-header-status', ios, 0)
line = '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%'
call check_char('pre-read-namelist-value', line, '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
read(u,'(a)',iostat=ios) line(1:len(line))
call check_int('delim-apostrophe-namelist-status', ios, 0)
pos = index(line, '''')
call check_true('delim-apostrophe-namelist-opening', pos > 0)
call check_int('delim-apostrophe-namelist-substring-len', len(line(pos:pos+5)), 6)
call check_char('delim-apostrophe-namelist-substring', line(pos:pos+5), "'A''B'")
close(u, status='delete')
call finish_checks(14)
end program p
