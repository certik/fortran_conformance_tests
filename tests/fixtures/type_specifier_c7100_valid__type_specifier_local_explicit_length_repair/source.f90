module specifier_definitions
implicit none
type :: record(k,n)
integer, kind :: k
integer, len :: n
integer :: payload
end type record
contains
subroutine local_context()
type(record(k=7,n=3)) :: value
value%payload=0
end subroutine local_context
end module specifier_definitions
