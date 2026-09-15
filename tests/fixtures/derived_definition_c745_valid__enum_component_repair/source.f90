module definitions
implicit none
enum, bind(c) :: category
enumerator :: one=1
end enum
type :: record
sequence
integer :: payload
end type
end module
