program p
implicit none
integer :: u, value
open(newunit=u, status='scratch', form='formatted', access='sequential')
read(u,decimal='POINT') value
end program p
