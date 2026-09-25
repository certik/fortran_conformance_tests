program p
implicit none
integer :: value
character(len=40) :: rec
rec = '&grp value=7 /'
value = -1
read(rec,nml=value)
end program p
