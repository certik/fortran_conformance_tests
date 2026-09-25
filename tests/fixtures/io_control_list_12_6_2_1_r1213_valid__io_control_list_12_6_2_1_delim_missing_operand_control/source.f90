program p
implicit none
integer :: u
open(newunit=u,status='scratch',form='formatted')
write(unit=u, fmt=*, delim='QUOTE') 'a'
close(u)
end program p
