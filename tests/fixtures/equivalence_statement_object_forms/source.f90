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
integer :: s, t, spare
integer :: wa(3), wb(3)
integer :: ea(4), eb(3)
character(4) :: cs
character(2) :: ds
character(3) :: ca(2)
character(1) :: da
equivalence (s, t)
equivalence (wa, wb)
equivalence (ea(3), eb(1))
equivalence (cs(2:3), ds)
equivalence (ca(2)(2:2), da)
s = -141
t = -252
spare = -363
wa = -474
wb = -585
ea = -696
eb = -707
cs = '####'
ds = '@@'
ca = '###'
da = '@'
call check_integer('scalar-pre', s, -252)
call check_integer('whole-array-pre', wa(2), -585)
call check_integer('array-element-pre', ea(4), -707)
call check_character('scalar-substring-pre', cs(3:3), '@')
call check_character('array-element-substring-pre', ca(2)(2:2), '@')
t = 41
wb(2) = 43
eb(2) = 47
ds(2:2) = 'Q'
da = 'R'
call check_integer('scalar-alias', s, 41)
call check_integer('whole-array-alias', wa(2), 43)
call check_integer('array-element-alias', ea(4), 47)
call check_character('scalar-substring-alias', cs(3:3), 'Q')
call check_character('array-element-substring-alias', ca(2)(2:2), 'R')
call finish_checks(10)
write(*,'(a)') 'EQUIVALENCE STATEMENT OBJECT_FORMS OK'
end program p
