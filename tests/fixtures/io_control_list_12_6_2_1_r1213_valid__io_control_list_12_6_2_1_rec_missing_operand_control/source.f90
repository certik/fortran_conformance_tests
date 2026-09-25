program p
implicit none
integer :: u,value
open(newunit=u,status='scratch',form='formatted',access='direct',recl=1)
write(u,'(I1)',rec=1) 7; value=-1
read(u,'(I1)',rec=1) value
if(value/=7) error stop 1
close(u)
end program p
