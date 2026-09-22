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
integer, parameter :: k=kind(0)
integer(kind=k) :: left_k, right_k
character(len=2) :: left_c, right_c
left_k=89
right_k=97
left_c='AB'
right_c='CD'
associate(a_integer_kind=>[left_k,right_k])
call check_integer('integer_kind:rank',rank(a_integer_kind),1)
call check_integer('integer_kind:size',size(a_integer_kind),2)
call check_integer('integer_kind:kind',kind(a_integer_kind),k)
call check_integer('integer_kind:value-1',a_integer_kind(1),89)
call check_integer('integer_kind:value-2',a_integer_kind(2),97)
end associate
associate(a_character_inferred=>[left_c,right_c])
call check_integer('character_inferred:rank',rank(a_character_inferred),1)
call check_integer('character_inferred:size',size(a_character_inferred),2)
call check_integer('character_inferred:length',len(a_character_inferred),2)
call check_logical('character_inferred:value-1',a_character_inferred(1)=='AB',.true.)
call check_logical('character_inferred:value-2',a_character_inferred(2)=='CD',.true.)
end associate
call finish_checks(10)
contains
end program p
