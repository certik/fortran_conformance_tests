module specifier_definitions
implicit none
type :: record(k,n,pad)
integer, kind :: k
integer, len :: n
integer, len :: pad=5
integer :: payload
end type record
type(record(n=3)) :: value
end module specifier_definitions
