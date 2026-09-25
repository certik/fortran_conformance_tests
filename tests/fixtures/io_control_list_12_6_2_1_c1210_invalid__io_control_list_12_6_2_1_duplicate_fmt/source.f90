program p
implicit none
integer :: value
character(len=1) :: rec
rec = '7'
value = -1
read(rec,fmt='(I1)',fmt='(I1)') value
end program p
