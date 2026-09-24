program p
integer :: u, ios
character(len=20) :: msg
msg = 'sentinel'
open(newunit=u, status='scratch', iostat=ios, iomsg=msg)
close(u, status='delete')
end program p
