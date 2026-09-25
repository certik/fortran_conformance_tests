program p
implicit none
integer :: u, id
if (.false.) then
  write(u,'(I1)',asynchronous='YES',id=id) 7
end if
end program p
