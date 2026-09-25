program p
implicit none
integer :: u, id
open(newunit=u, status='scratch', form='formatted', access='sequential')
id = -2
write(u,'(I1)',id=id) 7
end program p
