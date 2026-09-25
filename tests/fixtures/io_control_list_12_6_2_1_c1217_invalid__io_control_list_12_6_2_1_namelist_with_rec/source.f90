program p
implicit none
integer :: u, value
namelist /grp/ value
open(newunit=u, status='scratch', form='formatted', access='direct', recl=40)
value = 1
write(u,nml=grp,rec=1)
read(u,nml=grp,rec=1)
close(u)
end program p
