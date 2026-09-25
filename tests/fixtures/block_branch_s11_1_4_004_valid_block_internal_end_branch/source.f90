program block_internal_end_branch
implicit none
integer :: value
value=5
block
  value=11
  go to 100
  value=-99
100 end block
if (value /= 11) error stop 1
write(*,'(a)') 'BLOCK INTERNAL END BRANCH OK'
end program block_internal_end_branch
