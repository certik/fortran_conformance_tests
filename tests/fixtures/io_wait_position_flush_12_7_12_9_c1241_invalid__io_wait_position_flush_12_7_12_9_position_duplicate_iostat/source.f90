program p
implicit none
integer :: u, ios, ios2
open(newunit=u, status='scratch', form='formatted', action='readwrite')
rewind(unit=u, iostat=ios, iostat=ios2)
end program p
