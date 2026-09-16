module functions
implicit none
contains
pure integer function extent(n)
integer, intent(in) :: n
extent = n
end function
end module
