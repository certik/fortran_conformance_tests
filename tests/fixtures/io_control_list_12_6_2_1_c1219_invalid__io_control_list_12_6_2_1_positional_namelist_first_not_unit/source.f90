program p
implicit none
integer :: value
character(len=40) :: rec
namelist /grp/ value
rec = '&grp value=7 /'
value = -1
read(err=100, grp, unit=rec)
100 continue
end program p
