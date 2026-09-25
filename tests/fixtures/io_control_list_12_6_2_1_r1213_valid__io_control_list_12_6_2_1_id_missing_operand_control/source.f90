program p
implicit none
integer :: u,id
open(newunit=u,status='scratch',form='formatted',asynchronous='yes')
id=-1
write(u,'(I1)',asynchronous='YES',id=id) 7
close(u)
end program p
