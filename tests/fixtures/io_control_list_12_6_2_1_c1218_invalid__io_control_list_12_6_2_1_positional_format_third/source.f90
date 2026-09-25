program p
implicit none
integer :: value, ios
character(len=1) :: rec
rec = '7'
value = -1
read(unit=rec, iostat=ios, '(I1)') value
end program p
