module definitions
implicit none
enum, bind(c) :: category
enumerator :: zero=0, one=1
end enum
type :: record
    type(category) :: field
end type
end module
