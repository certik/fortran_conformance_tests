subroutine character_selector(n)
implicit none
integer, intent(in) :: n
character(len=n), save :: text
text='x'
end subroutine character_selector
