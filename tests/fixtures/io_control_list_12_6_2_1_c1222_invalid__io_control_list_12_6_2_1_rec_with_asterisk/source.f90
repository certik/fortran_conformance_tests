program p
implicit none
integer :: u, value
open(newunit=u, status='scratch', form='formatted', access='sequential')
read(u,*,rec=1) value
end program p
