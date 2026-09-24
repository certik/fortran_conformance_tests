program p
integer :: u
open(newunit=u, file=123, status='replace')
close(u, status='delete')
end program p
