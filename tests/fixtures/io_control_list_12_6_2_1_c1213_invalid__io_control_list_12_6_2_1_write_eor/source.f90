program p
implicit none
integer :: u
open(newunit=u, status='scratch', form='formatted', access='sequential')
write(u,'(I1)',advance='NO',eor=100) 7
100 continue
end program p
