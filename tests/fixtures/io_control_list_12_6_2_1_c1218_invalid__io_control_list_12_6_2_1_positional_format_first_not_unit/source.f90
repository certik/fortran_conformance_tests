program p
implicit none
integer :: value
character(len=1) :: rec
rec = '7'
value = -1
read(err=100, '(I1)', unit=rec) value
100 continue
end program p
