program p
implicit none
integer :: value
character(len=40) :: rec
namelist /grp/ value
rec = '&grp value=7 /'
value = -1
read(rec,nml=grp) value
end program p
