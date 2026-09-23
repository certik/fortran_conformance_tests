module equivalence_statement_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, check_character, finish_checks
contains
subroutine check_integer(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
  write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_INTEGER', label, actual, expected
  error stop 10
end if
checked = checked + 1
end subroutine check_integer
subroutine check_logical(label, actual, expected)
character(*), intent(in) :: label
logical, intent(in) :: actual, expected
if (actual .neqv. expected) then
  write(*,'(a,1x,a,1x,l1,1x,l1)') 'CHECK_LOGICAL', label, actual, expected
  error stop 11
end if
checked = checked + 1
end subroutine check_logical
subroutine check_character(label, actual, expected)
character(*), intent(in) :: label, actual, expected
if (len(actual) /= len(expected)) then
  write(*,'(a,1x,a,1x,i0,1x,i0)') 'CHECK_CHARACTER_LEN', label, len(actual), len(expected)
  error stop 12
end if
if (actual /= expected) then
  write(*,'(a,1x,a,1x,a,1x,a)') 'CHECK_CHARACTER', label, actual, expected
  error stop 13
end if
checked = checked + 1
end subroutine check_character
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
  write(*,'(a,1x,i0,1x,i0)') 'CHECK_COUNT', checked, expected
  error stop 14
end if
end subroutine finish_checks
end module equivalence_statement_checks
program p
use equivalence_statement_checks, only: check_integer, check_logical, check_character, finish_checks
implicit none
character(3) :: c
character(1) :: d
equivalence (c(2:2), d)
c = '###'
d = '@'
call check_character('one-character-pre', c(2:2), '@')
d = 'Z'
call check_character('one-character-alias', c(2:2), 'Z')
call finish_checks(2)
write(*,'(a)') 'EQUIVALENCE STATEMENT ONE_CHARACTER_SUBSTRING OK'
end program p
