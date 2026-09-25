program p
implicit none
integer :: u, value
open(newunit=u, status='scratch', form='formatted', access='sequential')
read(u,pad='YES') value
end program p
