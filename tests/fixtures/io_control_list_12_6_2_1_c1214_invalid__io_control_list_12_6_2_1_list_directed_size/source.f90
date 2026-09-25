program p
implicit none
integer :: value, n
character(len=1) :: rec
rec = '7'
value = -1
read(rec,*,size=n) value
end program p
