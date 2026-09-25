program p
implicit none
integer :: value
character(len=1) :: rec
rec='7'; value=-1
read(rec,'(I1)',err=100) value
contains
subroutine q()
100 continue
end subroutine q
end program p
