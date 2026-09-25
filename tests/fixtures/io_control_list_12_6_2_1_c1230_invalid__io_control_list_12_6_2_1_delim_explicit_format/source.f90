program p
implicit none
integer :: u
open(newunit=u, status='scratch', form='formatted', access='sequential')
write(u,'(A)',delim='QUOTE') 'a'
end program p
