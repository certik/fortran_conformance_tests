module array_value_checks
implicit none
private
integer, save :: checked=0
public :: check_integer, check_logical, finish_checks
contains
subroutine check_integer(label,actual,expected)
character(*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'CHECK_INTEGER',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(*), intent(in) :: label
logical, intent(in) :: actual,expected
if (actual .neqv. expected) then
print *, 'CHECK_LOGICAL',label,'ACTUAL',actual,'EXPECTED',expected
error stop 2
end if
checked=checked+1
end subroutine check_logical
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked/=expected) then
print *, 'CHECK_COUNT',checked,'EXPECTED',expected
error stop 3
end if
end subroutine finish_checks
end module array_value_checks
program p
use array_value_checks, only: check_integer, check_logical, finish_checks
implicit none
character(len=3), parameter :: text='ABC'
integer :: i
associate(a_pad_truncate=>[character(len=3) :: 'A','BCDE'])
call check_integer('pad_truncate:rank',rank(a_pad_truncate),1)
call check_integer('pad_truncate:size',size(a_pad_truncate),2)
call check_integer('pad_truncate:length',len(a_pad_truncate),3)
call check_logical('pad_truncate:value-1',a_pad_truncate(1)=='A  ',.true.)
call check_logical('pad_truncate:value-2',a_pad_truncate(2)=='BCD',.true.)
end associate
associate(a_dependent_substrings=>[character(len=3) :: (text(1:i),i=1,3)])
call check_integer('dependent_substrings:rank',rank(a_dependent_substrings),1)
call check_integer('dependent_substrings:size',size(a_dependent_substrings),3)
call check_integer('dependent_substrings:length',len(a_dependent_substrings),3)
call check_logical('dependent_substrings:value-1',a_dependent_substrings(1)=='A  ',.true.)
call check_logical('dependent_substrings:value-2',a_dependent_substrings(2)=='AB ',.true.)
call check_logical('dependent_substrings:value-3',a_dependent_substrings(3)=='ABC',.true.)
end associate
call finish_checks(11)
contains
end program p
