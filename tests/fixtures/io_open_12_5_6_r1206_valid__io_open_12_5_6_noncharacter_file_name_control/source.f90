program p
integer :: u
open(newunit=u, file='io_open_r1206_control.dat', status='replace')
close(u, status='delete')
end program p
