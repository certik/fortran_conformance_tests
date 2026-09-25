program p
implicit none
integer :: value, ios
character(len=40) :: rec
namelist /grp/ value
if (.false.) then
  read(rec, grp, iostat=ios)
end if
end program p
