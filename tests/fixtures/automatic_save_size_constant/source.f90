subroutine size_constant()
implicit none
integer :: basis(3)
integer, save :: a(size(basis))
a=1
end subroutine size_constant
