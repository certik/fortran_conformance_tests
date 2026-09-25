program p
implicit none
integer :: u,value
open(newunit=u,status='scratch',form='formatted')
write(u,'(A)') '7'; rewind(u); value=-1
read(u,'(I1)',advance='NO') value
if(value/=7) error stop 1
close(u)
end program p
