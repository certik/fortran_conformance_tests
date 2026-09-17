subroutine len_constant()
implicit none
character(len=3) :: basis
character(len=len(basis)), save :: text
text='abc'
end subroutine len_constant
