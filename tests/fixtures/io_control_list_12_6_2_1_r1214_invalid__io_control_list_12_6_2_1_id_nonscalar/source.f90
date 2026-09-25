program p
implicit none
integer :: u, id(1)
open(newunit=u, status='scratch', form='formatted', access='sequential')
id = -2
write(u,'(I1)',asynchronous='YES',id=id) 7
end program p
