program p
implicit none
integer :: checked
integer :: n,entries
checked=0
entries=0
n=3
outer_scope: block
character(len=n) :: outer_text
entries=entries+1
call check_integer('nested_outer:entry',entries,1)
outer_text='abc'
n=5
call check_integer('nested:before-inner-source',n,5)
inner_scope: block
character(len=n) :: inner_text
entries=entries+1
call check_integer('nested_inner:entry',entries,2)
inner_text='abcde'
n=7
call check_integer('nested:inside-source',n,7)
call check_integer('nested_outer:length',len(outer_text),3)
call check_logical('nested_outer:payload',outer_text=='abc',.true.)
call check_integer('nested_inner:length',len(inner_text),5)
call check_logical('nested_inner:payload',inner_text=='abcde',.true.)
end block inner_scope
call check_integer('nested_outer_after_inner:length',len(outer_text),3)
call check_logical('nested_outer_after_inner:payload',outer_text=='abc',.true.)
end block outer_scope
call check_integer('nested:entries',entries,2)
call finish_checks(11)
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
