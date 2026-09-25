program block_name_match_control
implicit none
integer :: value
value=0
block
  value=17
end block stray_name
if (value /= 17) error stop 1
write(*,'(a)') 'BLOCK NAME MATCH OK'
end program block_name_match_control
