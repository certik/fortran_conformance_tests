program p
implicit none
integer :: value, ios
character(len=1) :: rec
character(len=40) :: msg
rec='7'; value=-1; ios=-1; msg='sentinel'
read(rec,'(I1)',iostat=ios,iomsg=msg) value
if(value/=7 .or. ios/=0) error stop 1
end program p
