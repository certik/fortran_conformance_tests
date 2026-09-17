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
integer :: empty(0)
integer :: i
call check_integer('integer_control:size',size([7]),1)
call observe_integer_control([7])
call check_integer('typed_empty:size',size([integer ::]),0)
call observe_typed_empty([integer ::])
call check_integer('zero_trip:size',size([(i,i=1,0)]),0)
call observe_zero_trip([(i,i=1,0)])
call check_integer('empty_source:size',size([11,empty,13]),2)
call observe_empty_source([11,empty,13])
call finish_checks(15)
contains
subroutine observe_integer_control(a)
integer, intent(in) :: a(..)
call check_integer('integer_control:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('integer_control:argument-size',size(a),1)
call check_integer('integer_control:value-1',a(1),7)
rank default
print *, 'UNEXPECTED_RANK','integer_control',rank(a)
error stop 4
end select
end subroutine observe_integer_control
subroutine observe_typed_empty(a)
integer, intent(in) :: a(..)
call check_integer('typed_empty:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('typed_empty:argument-size',size(a),0)
rank default
print *, 'UNEXPECTED_RANK','typed_empty',rank(a)
error stop 4
end select
end subroutine observe_typed_empty
subroutine observe_zero_trip(a)
integer, intent(in) :: a(..)
call check_integer('zero_trip:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('zero_trip:argument-size',size(a),0)
rank default
print *, 'UNEXPECTED_RANK','zero_trip',rank(a)
error stop 4
end select
end subroutine observe_zero_trip
subroutine observe_empty_source(a)
integer, intent(in) :: a(..)
call check_integer('empty_source:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('empty_source:argument-size',size(a),2)
call check_integer('empty_source:value-1',a(1),11)
call check_integer('empty_source:value-2',a(2),13)
rank default
print *, 'UNEXPECTED_RANK','empty_source',rank(a)
error stop 4
end select
end subroutine observe_empty_source
end program p
