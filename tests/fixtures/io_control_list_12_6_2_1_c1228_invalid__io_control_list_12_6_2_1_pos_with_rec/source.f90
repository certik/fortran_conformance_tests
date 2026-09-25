program p
implicit none
integer :: u, value
open(newunit=u, status='scratch', form='formatted', access='sequential')
read(u,'(I1)',pos=1,rec=1) value
end program p
