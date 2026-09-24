program p
implicit none
character(len=4) :: c(2)
integer :: idx(2)
idx = [1, 2]
write(c(idx),'(a)') 'AB'
end program p
