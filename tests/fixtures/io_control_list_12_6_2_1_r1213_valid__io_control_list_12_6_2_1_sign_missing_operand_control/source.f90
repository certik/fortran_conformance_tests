program p
implicit none
integer :: u
open(newunit=u, status='scratch', form='formatted')
write(unit=u, fmt='(I1)') 7
close(u)
end program p
