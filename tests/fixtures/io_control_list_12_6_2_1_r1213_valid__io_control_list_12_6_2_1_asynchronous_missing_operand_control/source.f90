program p
implicit none
integer :: u
open(newunit=u,status='scratch',form='formatted')
write(u,'(I1)',asynchronous='NO') 7
close(u)
end program p
