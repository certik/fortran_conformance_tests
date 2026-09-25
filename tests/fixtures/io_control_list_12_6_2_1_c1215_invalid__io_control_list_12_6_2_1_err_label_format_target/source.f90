program p
implicit none
integer :: value
character(len=1) :: rec
rec='7'; value=-1
read(rec,'(I1)',err=100) value
100 format(I1)
end program p
