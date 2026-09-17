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
integer :: vector(2)
integer :: i,j
vector(1)=31
vector(2)=37
call check_integer('nested:size',size([((10*i+j,j=1,i),i=1,3)]),6)
call observe_nested([((10*i+j,j=1,i),i=1,3)])
call check_integer('array_body:size',size([(vector+i,i=1,2)]),4)
call observe_array_body([(vector+i,i=1,2)])
call finish_checks(16)
contains
subroutine observe_nested(a)
integer, intent(in) :: a(..)
call check_integer('nested:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('nested:argument-size',size(a),6)
call check_integer('nested:value-1',a(1),11)
call check_integer('nested:value-2',a(2),21)
call check_integer('nested:value-3',a(3),22)
call check_integer('nested:value-4',a(4),31)
call check_integer('nested:value-5',a(5),32)
call check_integer('nested:value-6',a(6),33)
rank default
print *, 'UNEXPECTED_RANK','nested',rank(a)
error stop 4
end select
end subroutine observe_nested
subroutine observe_array_body(a)
integer, intent(in) :: a(..)
call check_integer('array_body:rank',rank(a),1)
select rank(a)
rank(1)
call check_integer('array_body:argument-size',size(a),4)
call check_integer('array_body:value-1',a(1),32)
call check_integer('array_body:value-2',a(2),38)
call check_integer('array_body:value-3',a(3),33)
call check_integer('array_body:value-4',a(4),39)
rank default
print *, 'UNEXPECTED_RANK','array_body',rank(a)
error stop 4
end select
end subroutine observe_array_body
end program p
