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
integer, parameter :: k = 2
integer :: a(5), b(3)
character(3) :: left_start, left_end
character(4) :: left_both
character(2) :: peer_start, peer_end
character(4) :: peer_both
equivalence (a(k+1), b(1))
equivalence (left_start(:2), peer_start)
equivalence (left_end(2:), peer_end)
equivalence (left_both(:), peer_both)
a = -151
b = -262
left_start = '###'
left_end = '###'
left_both = '####'
peer_start = '@@'
peer_end = '@@'
peer_both = '@@@@'
call check_integer('named-constant-pre', a(k+2), -262)
call check_character('omitted-start-pre', left_start(2:2), '@')
call check_character('omitted-end-pre', left_end(3:3), '@')
call check_character('omitted-both-pre', left_both(1:1), '@')
b(2) = 53
peer_start(2:2) = 'M'
peer_end(2:2) = 'N'
peer_both(1:1) = 'P'
call check_integer('named-constant-alias', a(k+2), 53)
call check_character('omitted-start-alias', left_start(2:2), 'M')
call check_character('omitted-end-alias', left_end(3:3), 'N')
call check_character('omitted-both-alias', left_both(1:1), 'P')
call finish_checks(8)
write(*,'(a)') 'EQUIVALENCE STATEMENT CONSTANT_EXPRESSIONS OK'
end program p
