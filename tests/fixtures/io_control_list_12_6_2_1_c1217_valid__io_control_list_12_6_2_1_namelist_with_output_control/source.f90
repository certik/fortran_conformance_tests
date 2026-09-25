program p
implicit none
integer :: value, u
namelist /grp/ value
if (.false.) then
  write(u,nml=grp)
end if
end program p
