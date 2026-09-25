program block_ordinary_declaration_control
implicit none
integer :: result, local_value
result=-1
local_value=5
block
  integer :: local_value
  intent(in) :: local_value
  local_value=31
  result=local_value
end block
if (result /= 31) error stop 1
if (local_value /= 5) error stop 2
write(*,'(a)') 'BLOCK ORDINARY DECLARATION OK'
end program block_ordinary_declaration_control
