program p
implicit none
integer :: u, value
open(newunit=u,status='scratch',form='formatted')
value=-1
read(u,'(I2)',advance='NO',eor=100) value
contains
subroutine q()
100 continue
end subroutine q
end program p
