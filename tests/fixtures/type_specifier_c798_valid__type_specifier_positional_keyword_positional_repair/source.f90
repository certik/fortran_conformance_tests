module specifier_definitions
implicit none
type :: record(a,b,c,d)
integer, kind :: a=1
integer, kind :: b=2
integer, kind :: c=3
integer, kind :: d=4
integer :: payload
end type record
type(record(11,d=44,b=22)) :: value
end module specifier_definitions
