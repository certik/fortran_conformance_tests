program p
implicit none
integer :: value
character(len=40) :: rec
namelist /grp/ value
if (.false.) then
  read(rec,nml=grp)
end if
end program p
