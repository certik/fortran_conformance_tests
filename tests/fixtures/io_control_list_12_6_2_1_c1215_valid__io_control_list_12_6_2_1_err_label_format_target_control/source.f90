program p
implicit none
integer :: value
character(len=1) :: rec
rec='7'; value=-1
if (.false.) then
  read(rec,'(I1)',err=100) value
end if
100 continue
end program p
