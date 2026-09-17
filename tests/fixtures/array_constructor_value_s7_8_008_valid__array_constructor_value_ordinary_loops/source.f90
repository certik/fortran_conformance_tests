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
integer :: i
call check_integer('default_step:size',size([(i,i=1,3)]),3)
call observe_default_step([(i,i=1,3)])
call check_integer('positive_step:size',size([(i,i=1,5,2)]),3)
call observe_positive_step([(i,i=1,5,2)])
call check_integer('negative_step:size',size([(i,i=5,1,-2)]),3)
call observe_negative_step([(i,i=5,1,-2)])
call check_integer('multiple_body:size',size([(i,10*i,i=1,2)]),4)
call observe_multiple_body([(i,10*i,i=1,2)])
call finish_checks(25)
contains
subroutine observe_default_step(a)
integer, intent(in) :: a(..)
call check_integer('default_step:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('default_step:argument-size',size(a),3)
call check_integer('default_step:value-1',a(1),1)
call check_integer('default_step:value-2',a(2),2)
call check_integer('default_step:value-3',a(3),3)
rank default
print *, 'UNEXPECTED_RANK','default_step',rank(a)
error stop 4
end select
end subroutine observe_default_step
subroutine observe_positive_step(a)
integer, intent(in) :: a(..)
call check_integer('positive_step:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('positive_step:argument-size',size(a),3)
call check_integer('positive_step:value-1',a(1),1)
call check_integer('positive_step:value-2',a(2),3)
call check_integer('positive_step:value-3',a(3),5)
rank default
print *, 'UNEXPECTED_RANK','positive_step',rank(a)
error stop 4
end select
end subroutine observe_positive_step
subroutine observe_negative_step(a)
integer, intent(in) :: a(..)
call check_integer('negative_step:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('negative_step:argument-size',size(a),3)
call check_integer('negative_step:value-1',a(1),5)
call check_integer('negative_step:value-2',a(2),3)
call check_integer('negative_step:value-3',a(3),1)
rank default
print *, 'UNEXPECTED_RANK','negative_step',rank(a)
error stop 4
end select
end subroutine observe_negative_step
subroutine observe_multiple_body(a)
integer, intent(in) :: a(..)
call check_integer('multiple_body:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('multiple_body:argument-size',size(a),4)
call check_integer('multiple_body:value-1',a(1),1)
call check_integer('multiple_body:value-2',a(2),10)
call check_integer('multiple_body:value-3',a(3),2)
call check_integer('multiple_body:value-4',a(4),20)
rank default
print *, 'UNEXPECTED_RANK','multiple_body',rank(a)
error stop 4
end select
end subroutine observe_multiple_body
end program p
