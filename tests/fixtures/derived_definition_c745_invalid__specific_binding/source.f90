module definitions
implicit none
type :: record
    sequence
    integer :: payload
contains
    procedure, nopass :: answer
end type
contains
integer function answer()
    answer = 17
end function
end module
