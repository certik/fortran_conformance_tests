module specifier_definitions
implicit none
type :: record(k,n)
integer, kind :: k
integer, len :: n
integer :: payload
end type record
contains
subroutine select_record(item)
class(record(k=7,n=*)), intent(in) :: item
select type(view=>item)
type is(record(k=7,n=*))
continue
end select
end subroutine select_record
subroutine possible_caller()
type(record(k=7,n=5)) :: actual
actual%payload=0
call select_record(actual)
end subroutine possible_caller
end module specifier_definitions
