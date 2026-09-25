program p
implicit none
integer :: u, value
namelist /grp/ value
open(newunit=u, status='scratch', form='formatted', access='sequential')
value = 1
write(u,nml=grp)
rewind(u)
read(u,nml=grp)
close(u)
end program p
