program p
implicit none
integer :: value
character(len=40) :: rec
namelist /grp/ value
if (.false.) then
  read(rec, grp, err=100)
end if
100 continue
end program p
