program p
implicit none
integer :: u, value
open(newunit=u, status='scratch', form='formatted', access='sequential')
read(u,'(I1)',rec=1,end=100) value
100 continue
end program p
