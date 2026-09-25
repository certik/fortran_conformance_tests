program p
implicit none
integer :: u, id
open(newunit=u, status='scratch', form='formatted', access='sequential')
id = -2
write(u,'(I1)',asynchronous='NO',id=id) 7
end program p
