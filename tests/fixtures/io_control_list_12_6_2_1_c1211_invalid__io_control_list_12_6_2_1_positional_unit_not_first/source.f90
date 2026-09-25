program p
implicit none
integer :: value
character(len=1) :: rec
rec = '7'
value = -1
read(fmt='(I1)', rec) value
end program p
