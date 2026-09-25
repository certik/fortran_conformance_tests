program p
implicit none
integer :: u
open(newunit=u, status='scratch', form='formatted', access='sequential')
write(u,'(I1)',pad='YES') 7
end program p
