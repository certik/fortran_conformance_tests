module specifier_definitions
implicit none
type :: record(k,n,pad)
integer, kind :: k
integer, len :: n
integer, len :: pad=5
integer :: payload
end type record
type(record(k=7)) :: value
end module specifier_definitions
