program p
implicit none
integer :: value, ios
character(len=40) :: rec
namelist /grp/ value
rec = '&grp value=7 /'
value = -1
read(unit=rec, iostat=ios, grp)
end program p
