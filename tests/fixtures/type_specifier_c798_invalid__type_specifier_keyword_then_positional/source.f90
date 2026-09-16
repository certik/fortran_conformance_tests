module specifier_definitions
implicit none
type :: record(a,b,c)
integer, kind :: a=1
integer, kind :: b=2
integer, kind :: c=3
integer :: payload
end type record
type(record(c=31,11)) :: value
end module specifier_definitions
