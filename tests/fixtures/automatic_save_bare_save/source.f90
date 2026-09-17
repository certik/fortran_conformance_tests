subroutine bare_save(n)
implicit none
integer, intent(in) :: n
character(len=n) :: text
save
text='x'
end subroutine bare_save
