program p
implicit none
integer :: value, u
namelist /grp/ value
value = -1
write(u,nml=grp) value
end program p
