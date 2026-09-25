program p
implicit none
integer :: u, value
open(newunit=u,status='scratch',form='formatted')
value=-1
read(u,'(I1)',end=100) value
100 format(I1)
end program p
