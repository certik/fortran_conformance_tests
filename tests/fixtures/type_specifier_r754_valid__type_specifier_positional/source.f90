module specifier_definitions
implicit none
type :: record(k,n)
integer, kind :: k=7
integer, len :: n=3
integer :: payload
end type record
type(record(5,11)) :: value
end module specifier_definitions
