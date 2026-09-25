program p
implicit none
integer :: value
character(len=1) :: rec
if (.false.) then
  read(rec,'(I1)') value
end if
end program p
