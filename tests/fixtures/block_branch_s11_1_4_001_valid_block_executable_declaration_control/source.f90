program block_executable_declaration_control
implicit none
integer :: before_event, body_event, after_event, local_marker
before_event=11
body_event=-1
after_event=-1
local_marker=99
block
  integer :: local_marker
  local_marker=23
  if (before_event /= 11) error stop 1
  body_event=local_marker
end block
after_event=37
if (body_event /= 23) error stop 2
if (after_event /= 37) error stop 3
if (local_marker /= 99) error stop 4
write(*,'(a)') 'BLOCK EXECUTABLE DECLARATION OK'
end program block_executable_declaration_control
