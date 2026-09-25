program p
implicit none
integer :: u, value
open(newunit=u,status='scratch',form='formatted')
value=-1
if (.false.) then
  read(u,'(I2)',advance='NO',eor=100) value
end if
100 continue
end program p
