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
integer :: n
n=3
call check_integer('character_control:size',size([character(len=3) :: 'abc']),1)
call check_integer('character_control:length',len([character(len=3) :: 'abc']),3)
call observe_character_control([character(len=3) :: 'abc'])
call check_integer('character_fixed:size',size([character(len=3) ::]),0)
call check_integer('character_fixed:length',len([character(len=3) ::]),3)
call observe_character_fixed([character(len=3) ::])
call check_integer('character_runtime:size',size([character(len=n) ::]),0)
call check_integer('character_runtime:length',len([character(len=n) ::]),3)
call observe_character_runtime([character(len=n) ::])
call finish_checks(16)
contains
subroutine observe_character_control(a)
character(len=*), intent(in) :: a(..)
call check_integer('character_control:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('character_control:argument-size',size(a),1)
call check_integer('character_control:argument-length',len(a),3)
call check_logical('character_control:value-1',a(1)=='abc',.true.)
rank default
print *, 'UNEXPECTED_RANK','character_control',rank(a)
error stop 4
end select
end subroutine observe_character_control
subroutine observe_character_fixed(a)
character(len=*), intent(in) :: a(..)
call check_integer('character_fixed:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('character_fixed:argument-size',size(a),0)
call check_integer('character_fixed:argument-length',len(a),3)
rank default
print *, 'UNEXPECTED_RANK','character_fixed',rank(a)
error stop 4
end select
end subroutine observe_character_fixed
subroutine observe_character_runtime(a)
character(len=*), intent(in) :: a(..)
call check_integer('character_runtime:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('character_runtime:argument-size',size(a),0)
call check_integer('character_runtime:argument-length',len(a),3)
rank default
print *, 'UNEXPECTED_RANK','character_runtime',rank(a)
error stop 4
end select
end subroutine observe_character_runtime
end program p
