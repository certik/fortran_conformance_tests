program p
implicit none
integer :: value, n
character(len=40) :: rec
namelist /grp/ value
rec = '&grp value=7 /'
value = -1
read(rec,nml=grp,size=n)
end program p
