program block_local_homonym_scope
implicit none
integer :: value, inside_value, outside_value
value=101
inside_value=-1
outside_value=-1
block
  integer :: value
  value=7
  if (value /= 7) error stop 1
  value=9
  inside_value=value
end block
outside_value=value
if (inside_value /= 9) error stop 2
if (outside_value /= 101) error stop 3
write(*,'(a)') 'BLOCK LOCAL HOMONYM OK'
end program block_local_homonym_scope
