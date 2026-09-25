program p
implicit none
integer :: value, ios
character(len=1) :: rec
if (.false.) then
  read(rec, '(I1)', iostat=ios) value
end if
end program p
