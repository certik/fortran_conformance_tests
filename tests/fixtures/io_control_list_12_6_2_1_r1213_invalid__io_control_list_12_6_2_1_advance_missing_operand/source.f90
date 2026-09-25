program p
implicit none
integer :: value, u, ios
character(len=40) :: rec
rec = '7'; value = -1; u = 10; ios = -1
read(u,'(I1)',advance=) value
end program p
