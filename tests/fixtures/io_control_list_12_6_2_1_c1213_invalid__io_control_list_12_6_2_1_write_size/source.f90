program p
implicit none
integer :: u, n
open(newunit=u, status='scratch', form='formatted', access='sequential')
write(u,'(I1)',size=n) 7
end program p
