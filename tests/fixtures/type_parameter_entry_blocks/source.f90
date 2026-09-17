program p
implicit none
integer :: checked
integer :: n,entries
checked=0
entries=0
n=3
block_selector: block
character(len=n) :: text
entries=entries+1
call check_integer('block_selector:entry',entries,1)
text='abc'
n=7
call check_integer('block_selector:source-now',n,7)
call check_integer('block_selector:length',len(text),3)
call check_logical('block_selector:payload',text=='abc',.true.)
end block block_selector
n=2
block_entity: block
character :: text*(n)
entries=entries+1
call check_integer('block_entity:entry',entries,2)
text='ab'
n=5
call check_integer('block_entity:source-now',n,5)
call check_integer('block_entity:length',len(text),2)
call check_logical('block_entity:payload',text=='ab',.true.)
end block block_entity
call check_integer('blocks:entries',entries,2)
call finish_checks(9)
contains
subroutine check_integer(label,actual,expected)
character(len=*), intent(in) :: label
integer, intent(in) :: actual,expected
if (actual/=expected) then
print *, 'CHECK_INTEGER',label,'ACTUAL',actual,'EXPECTED',expected
error stop 1
end if
checked=checked+1
end subroutine check_integer
subroutine check_logical(label,actual,expected)
character(len=*), intent(in) :: label
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
end program p
